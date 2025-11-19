from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionSettings(BaseModel):
    """User-configurable settings for transcription requests."""

    language: Optional[str] = Field(
        default=None,
        description="Optional BCP-47 language code to bias the ASR model towards a language.",
    )
    model: str = Field(
        default="parakeet_v3",
        description="Selected Pipecat model identifier to execute for transcription.",
    )
    streaming_mode: str = Field(
        default="batch",
        description="Whether to stream partial results or run a batch decode pipeline.",
    )
    input_device: Optional[str] = Field(
        default=None,
        description="Device ID for the capture source (e.g. microphone) chosen by the client.",
    )
    output_device: Optional[str] = Field(
        default=None,
        description="Device ID for playback/notifications when supported by the desktop wrapper.",
    )
    input_source: Optional[str] = Field(
        default="file",
        description="Indicates whether the request originated from a file upload or a live capture.",
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
