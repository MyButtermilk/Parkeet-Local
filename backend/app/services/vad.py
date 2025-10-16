from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import onnxruntime as ort

from app.config import Settings, get_settings
from app.services.model_registry import get_registry


@dataclass
class SpeechSegment:
    start: int
    end: int


class SileroVAD:
    """Wrapper around the Silero Voice Activity Detection ONNX model."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.registry = get_registry(self.settings)
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
