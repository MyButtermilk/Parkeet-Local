from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """Audio device advertised by the desktop wrapper."""

    id: str = Field(..., description="Unique identifier for the device")
    label: str = Field(..., description="Human readable device name")
    kind: str = Field(..., description="input or output")


class ModelInfo(BaseModel):
    """Available Pipecat model option."""

    id: str
    label: str
    streaming: bool = False


class PipecatOptions(BaseModel):
    """Option metadata mirrored to the frontend."""

    models: List[ModelInfo] = Field(default_factory=list)
    streaming_modes: List[str] = Field(default_factory=list)
    input_devices: List[DeviceInfo] = Field(default_factory=list)
    output_devices: List[DeviceInfo] = Field(default_factory=list)
    default_hotkey: str = Field(default="Ctrl+Shift+Space")
    upload_endpoint: str = Field(default="/api/pipecat/transcriptions")


class HotkeyEvent(BaseModel):
    """Event emitted when the desktop hotkey is used."""

    hotkey: str = Field(..., description="Human readable hotkey combination")
    state: str = Field(..., description="toggle, start, stop or other semantic flag")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(
        default=None, description="Optional request identifier for correlation"
    )


class HotkeyRegistration(BaseModel):
    """Response acknowledging a hotkey registration."""

    hotkey: str
    registered: bool = True
    reason: Optional[str] = None
