from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import numpy as np
from loguru import logger

from app.config import Settings, get_settings
from app.models.requests import TranscriptionRequest
from app.models.responses import TranscriptSegment, TranscriptionResult
from app.services.model_registry import get_registry
from app.services.vad import SileroVAD
from app.utils.audio_utils import load_audio, save_waveform, split_segments


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


class ParakeetTranscriptionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.registry = get_registry(self.settings)
        self.vad = SileroVAD(self.settings)
        tokenizer = self.registry.get_tokenizer()
        self.vocab = DecoderVocabulary.from_tokenizer_dict(tokenizer)
        self.session = self.registry.get_asr_session()

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        request: TranscriptionRequest | None = None,
        filename: str | None = None,
    ) -> TranscriptionResult:
        request = request or TranscriptionRequest()
        waveform, sample_rate = load_audio(audio_bytes, self.settings.sample_rate)

        if request.settings.enable_vad:
            vad_segments = self.vad.detect(
                waveform, sample_rate, threshold=request.settings.vad_threshold
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
            tokens = self._infer(segment_waveform)
            text = self.vocab.decode(tokens)
            transcript_parts.append(text)
            end_time = offset + len(segment_waveform) / sample_rate
            text_segments.append(
                TranscriptSegment(
                    text=text,
                    start=offset,
                    end=end_time,
                    speaker="SPEAKER_1" if request.settings.diarization else None,
                    confidence=None,
                )
            )
            offset = end_time

        transcript_text = " ".join(part for part in transcript_parts if part)

        if request.settings.enable_punctuation:
            transcript_text = self._restore_punctuation(transcript_text)
            for segment in text_segments:
                segment.text = self._restore_punctuation(segment.text)

        request_id = request.request_id or str(uuid.uuid4())
        settings_applied = request.settings.dict(exclude_none=True)

        if filename:
            target = Path(self.settings.storage_dir) / request_id
            save_waveform(target.with_suffix(".wav"), waveform, sample_rate)

        return TranscriptionResult(
            request_id=request_id,
            text=transcript_text,
            duration=processed_duration,
            segments=text_segments,
            settings_applied=settings_applied,
        )

    def _infer(self, waveform: np.ndarray) -> Sequence[int]:
        inputs = self.session.get_inputs()
        if not inputs:
            raise RuntimeError("Parakeet ONNX session has no inputs")
        input_name = inputs[0].name
        audio = waveform.astype(np.float32)[np.newaxis, :]
        outputs = self.session.run(None, {input_name: audio})
        logits = outputs[0]
        token_ids = np.argmax(logits, axis=-1).flatten().tolist()
        return token_ids

    def _restore_punctuation(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return normalized
        normalized = normalized[0].upper() + normalized[1:]
        if normalized[-1] not in {".", "?", "!"}:
            normalized += "."
        return normalized
