from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionSettings(BaseModel):
    """User-configurable settings for transcription requests."""

    language: Optional[str] = Field(
        default=None,
        description="Optional BCP-47 language code to bias the ASR model towards a language.",
    )
    enable_punctuation: bool = Field(
        default=True,
        description="Whether to enable automatic punctuation restoration in the ASR pipeline.",
    )
    enable_vad: bool = Field(
        default=True,
        description="Toggle for running Silero VAD before ASR inference to trim silence.",
    )
    vad_threshold: Optional[float] = Field(
        default=None,
        description="Override for the probability threshold used by the VAD model.",
    )
    diarization: bool = Field(
        default=False,
        description="Whether to run the optional speaker diarization heuristic on transcripts.",
    )


class TranscriptionRequest(BaseModel):
    """Metadata describing a transcription job."""

    request_id: Optional[str] = Field(
        default=None,
        description="Optional identifier supplied by the client for correlation.",
    )
    settings: TranscriptionSettings = Field(
        default_factory=TranscriptionSettings,
        description="Settings that control how the audio will be processed.",
    )
