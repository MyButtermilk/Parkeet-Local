from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """A single segment of recognized speech."""

    text: str = Field(..., description="Recognized text for this segment.")
    start: float = Field(..., description="Segment start time in seconds.")
    end: float = Field(..., description="Segment end time in seconds.")
    speaker: Optional[str] = Field(
        default=None, description="Optional speaker label if diarization is enabled."
    )
    confidence: Optional[float] = Field(
        default=None, description="Optional confidence score for the segment."
    )


class TranscriptionResult(BaseModel):
    """Response payload returned after audio transcription."""

    request_id: Optional[str] = Field(
        default=None, description="Identifier passed through from the original request."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the transcript was created."
    )
    text: str = Field(..., description="Full concatenated transcript text.")
    duration: float = Field(..., description="Total processed audio duration in seconds.")
    segments: List[TranscriptSegment] = Field(
        default_factory=list, description="Detailed transcript segments."
    )
    settings_applied: dict = Field(
        default_factory=dict,
        description="Normalized settings that were applied during transcription.",
    )
