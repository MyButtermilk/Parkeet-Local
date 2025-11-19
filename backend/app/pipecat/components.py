from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import onnxruntime as ort
import requests
from loguru import logger

from app.pipecat.settings import PipecatSettings, get_pipecat_settings
from app.utils.audio_utils import load_audio, save_waveform, split_segments

PARAKEET_MODEL_URL = (
    "https://huggingface.co/onnx-community/parakeet-ctc-v3/resolve/main/model.onnx?download=1"
)
PARAKEET_TOKENIZER_URL = (
    "https://huggingface.co/onnx-community/parakeet-ctc-v3/resolve/main/tokenizer.json?download=1"
)
SILERO_VAD_URL = "https://huggingface.co/snakers4/silero-vad/resolve/main/models/silero_vad.onnx?download=1"


class PipecatModelRegistry:
    """Pipecat-flavored registry around the Parakeet model assets."""

    def __init__(self, settings: PipecatSettings | None = None) -> None:
        self.settings = settings or get_pipecat_settings()
        self._sessions: Dict[str, ort.InferenceSession] = {}
        self._tokenizer: Dict[str, Any] | None = None

    def ensure_resources(self) -> None:
        self._download_if_missing(self.settings.asr_model_path, PARAKEET_MODEL_URL)
        self._download_if_missing(self.settings.tokenizer_path, PARAKEET_TOKENIZER_URL)
        self._download_if_missing(self.settings.vad_model_path, SILERO_VAD_URL)

    def get_asr_session(self) -> ort.InferenceSession:
        if "asr" not in self._sessions:
            self.ensure_resources()
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._sessions["asr"] = ort.InferenceSession(
                str(self.settings.asr_model_path), providers=providers
            )
            logger.info("Loaded ASR model from {}", self.settings.asr_model_path)
        return self._sessions["asr"]

    def get_vad_session(self) -> ort.InferenceSession:
        if "vad" not in self._sessions:
            self.ensure_resources()
            providers = ["CPUExecutionProvider"]
            self._sessions["vad"] = ort.InferenceSession(
                str(self.settings.vad_model_path), providers=providers
            )
            logger.info("Loaded VAD model from {}", self.settings.vad_model_path)
        return self._sessions["vad"]

    def get_tokenizer(self) -> Dict[str, Any]:
        if self._tokenizer is None:
            self.ensure_resources()
            with self.settings.tokenizer_path.open("r", encoding="utf-8") as handle:
                self._tokenizer = json.load(handle)
        return self._tokenizer

    def _download_if_missing(self, path: Path, url: str) -> None:
        if path.exists():
            return
        logger.info("Downloading %s", url)
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        with path.open("wb") as destination:
            shutil.copyfileobj(response.raw, destination)
        logger.info("Downloaded resource to %s", path)


@dataclass
class DecoderVocabulary:
    tokens: Sequence[str]
    blank_id: int
    word_delimiter: str = " "

    @classmethod
    def from_tokenizer_dict(cls, tokenizer_dict: dict) -> "DecoderVocabulary":
        model = tokenizer_dict.get("model", {})
        vocab = model.get("vocab", {})
        tokens = [""] * len(vocab)
        for token, index in vocab.items():
            tokens[index] = token.replace("▁", " ")
        blank_id = tokenizer_dict.get("added_tokens", [{}])[0].get("id", len(tokens) - 1)
        return cls(tokens=tokens, blank_id=blank_id)

    def decode(self, token_ids: Sequence[int]) -> str:
        pieces: List[str] = []
        previous = None
        for token_id in token_ids:
            if token_id == self.blank_id or token_id == previous:
                previous = token_id
                continue
            pieces.append(self.tokens[token_id])
            previous = token_id
        text = "".join(pieces)
        return " ".join(text.split())


@dataclass
class SpeechSegment:
    start: int
    end: int


class PipecatVAD:
    def __init__(self, settings: PipecatSettings | None = None) -> None:
        self.settings = settings or get_pipecat_settings()
        self.registry = PipecatModelRegistry(self.settings)
        self.session: ort.InferenceSession = self.registry.get_vad_session()

    def detect(self, waveform: np.ndarray, sample_rate: int, threshold: float | None = None) -> List[SpeechSegment]:
        threshold = threshold or self.settings.vad_threshold
        stride = 512
        window = 1536
        probs: List[float] = []
        for start in range(0, len(waveform) - window, stride):
            chunk = waveform[start : start + window]
            ort_inputs = {
                "input": chunk.reshape(1, -1),
                "sr": np.array(sample_rate, dtype=np.int64),
            }
            (prob,) = self.session.run(None, ort_inputs)
            probs.append(float(prob.squeeze()))

        speech_segments: List[SpeechSegment] = []
        active = False
        seg_start = 0
        for index, prob in enumerate(probs):
            time_start = index * stride
            time_end = time_start + window
            if prob >= threshold and not active:
                active = True
                seg_start = time_start
            elif prob < threshold and active:
                active = False
                if time_end - seg_start >= self.settings.vad_min_speech_seconds * sample_rate:
                    speech_segments.append(SpeechSegment(seg_start, time_end))

        if active:
            speech_segments.append(SpeechSegment(seg_start, len(waveform)))

        merged: List[SpeechSegment] = []
        for segment in speech_segments:
            if not merged:
                merged.append(segment)
                continue
            prev = merged[-1]
            gap = segment.start - prev.end
            if gap / sample_rate <= self.settings.vad_min_silence_seconds:
                merged[-1] = SpeechSegment(prev.start, segment.end)
            else:
                merged.append(segment)

        return merged

    def extract(self, waveform: np.ndarray, segments: Iterable[SpeechSegment]) -> np.ndarray:
        pieces = [waveform[segment.start : segment.end] for segment in segments]
        if not pieces:
            return waveform
        return np.concatenate(pieces)


class PipecatDecoder:
    def __init__(self, registry: PipecatModelRegistry) -> None:
        tokenizer = registry.get_tokenizer()
        self.vocab = DecoderVocabulary.from_tokenizer_dict(tokenizer)

    def decode(self, logits: np.ndarray) -> List[int]:
        token_ids = np.argmax(logits, axis=-1).flatten().tolist()
        return token_ids

    def tokens_to_text(self, token_ids: Sequence[int]) -> str:
        return self.vocab.decode(token_ids)


class PipecatPipeline:
    def __init__(self, settings: PipecatSettings | None = None) -> None:
        self.settings = settings or get_pipecat_settings()
        self.registry = PipecatModelRegistry(self.settings)
        self.vad = PipecatVAD(self.settings)
        self.decoder = PipecatDecoder(self.registry)
        self.session = self.registry.get_asr_session()

    def transcribe(self, audio_bytes: bytes, *, request_settings: dict | None = None, filename: str | None = None):
        from app.pipecat.schemas import TranscriptSegment, TranscriptionResult

        waveform, sample_rate = load_audio(audio_bytes, self.settings.sample_rate)
        request_settings = request_settings or {}
        vad_enabled = request_settings.get("enable_vad", True)
        if vad_enabled:
            vad_segments = self.vad.detect(
                waveform, sample_rate, threshold=request_settings.get("vad_threshold")
            )
            if vad_segments:
                logger.debug("Detected %d speech segments via VAD", len(vad_segments))
                waveform = self.vad.extract(waveform, vad_segments)

        text_segments: List[TranscriptSegment] = []
        transcript_parts: List[str] = []
        processed_duration = len(waveform) / sample_rate
        offset = 0.0

        for segment_waveform in split_segments(
            waveform, sample_rate, self.settings.max_segment_seconds
        ):
            inputs = self.session.get_inputs()
            if not inputs:
                raise RuntimeError("ASR ONNX session has no inputs")
            input_name = inputs[0].name
            audio = segment_waveform.astype(np.float32)[np.newaxis, :]
            outputs = self.session.run(None, {input_name: audio})
            tokens = self.decoder.decode(outputs[0])
            text = self.decoder.tokens_to_text(tokens)
            transcript_parts.append(text)
            end_time = offset + len(segment_waveform) / sample_rate
            text_segments.append(
                TranscriptSegment(
                    text=text,
                    start=offset,
                    end=end_time,
                    speaker=request_settings.get("speaker_hint"),
                    confidence=None,
                )
            )
            offset = end_time

        transcript_text = " ".join(part for part in transcript_parts if part)
        if request_settings.get("enable_punctuation", True):
            transcript_text = self._restore_punctuation(transcript_text)
            for segment in text_segments:
                segment.text = self._restore_punctuation(segment.text)

        settings_applied = {k: v for k, v in request_settings.items() if v is not None}

        if filename:
            target = Path(self.settings.storage_dir) / (request_settings.get("request_id") or "transcript")
            save_waveform(target.with_suffix(".wav"), waveform, sample_rate)

        return TranscriptionResult(
            request_id=request_settings.get("request_id"),
            text=transcript_text,
            duration=processed_duration,
            segments=text_segments,
            settings_applied=settings_applied,
        )

    def _restore_punctuation(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return normalized
        normalized = normalized[0].upper() + normalized[1:]
        if normalized[-1] not in {".", "?", "!"}:
            normalized += "."
        return normalized
