from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionSettings(BaseModel):
    """Pipecat session options mapped to legacy request settings."""

    language: Optional[str] = Field(default=None)
    enable_punctuation: bool = Field(default=True)
    enable_vad: bool = Field(default=True)
    vad_threshold: Optional[float] = Field(default=None)
    diarization: bool = Field(default=False)


class SessionCreateRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional client-chosen session id")
    settings: SessionSettings = Field(default_factory=SessionSettings)


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptSegment(BaseModel):
    text: str = Field(..., description="Recognized text for this segment.")
    start: float = Field(..., description="Segment start time in seconds.")
    end: float = Field(..., description="Segment end time in seconds.")
    speaker: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None)


class TranscriptionRequest(BaseModel):
    request_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    settings: SessionSettings = Field(default_factory=SessionSettings)


class TranscriptionResult(BaseModel):
    request_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    text: str = Field(...)
    duration: float = Field(...)
    segments: List[TranscriptSegment] = Field(default_factory=list)
    settings_applied: dict = Field(default_factory=dict)
