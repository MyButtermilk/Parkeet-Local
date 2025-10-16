from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
import soundfile as sf


def load_audio(data: bytes, target_sample_rate: int) -> Tuple[np.ndarray, int]:
    """Load audio from a bytes object and resample to the target sample rate."""

    with io.BytesIO(data) as buffer:
        waveform, sample_rate = sf.read(buffer)

    if waveform.ndim == 2:
        waveform = waveform.mean(axis=1)

    if sample_rate != target_sample_rate:
        waveform = resample_audio(waveform, sample_rate, target_sample_rate)
        sample_rate = target_sample_rate

    return waveform.astype(np.float32), sample_rate


def resample_audio(waveform: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
    """Resample the waveform to the target sample rate using polyphase filtering."""

    if original_sr == target_sr:
        return waveform

    from scipy.signal import resample_poly

    gcd = np.gcd(original_sr, target_sr)
    up = target_sr // gcd
    down = original_sr // gcd
    return resample_poly(waveform, up, down).astype(np.float32)


def split_segments(
    waveform: np.ndarray,
    sample_rate: int,
    segment_seconds: float,
) -> Iterable[np.ndarray]:
    """Split a waveform into smaller segments."""

    segment_length = int(segment_seconds * sample_rate)
    for start in range(0, len(waveform), segment_length):
        end = min(start + segment_length, len(waveform))
        yield waveform[start:end]


def save_waveform(path: Path, waveform: np.ndarray, sample_rate: int) -> None:
    """Persist a waveform to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, waveform, sample_rate)
