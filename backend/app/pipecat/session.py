from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict

from app.pipecat.components import PipecatPipeline
from app.pipecat.schemas import SessionCreateRequest, SessionCreateResponse, SessionSettings, TranscriptionRequest
from app.pipecat.settings import PipecatSettings, get_pipecat_settings


@dataclass
class PipecatSession:
    session_id: str
    settings: SessionSettings
    pipeline: PipecatPipeline = field(default_factory=PipecatPipeline)


class SessionManager:
    def __init__(self, settings: PipecatSettings | None = None) -> None:
        self.settings = settings or get_pipecat_settings()
        self.sessions: Dict[str, PipecatSession] = {}

    def create_session(self, payload: SessionCreateRequest | None = None) -> SessionCreateResponse:
        payload = payload or SessionCreateRequest()
        session_id = payload.session_id or str(uuid.uuid4())
        pipeline = PipecatPipeline(self.settings)
        self.sessions[session_id] = PipecatSession(session_id=session_id, settings=payload.settings, pipeline=pipeline)
        return SessionCreateResponse(session_id=session_id)

    def get_session(self, session_id: str) -> PipecatSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = PipecatSession(
                session_id=session_id, settings=SessionSettings(), pipeline=PipecatPipeline(self.settings)
            )
        return self.sessions[session_id]

    def transcribe(self, session_id: str, request: TranscriptionRequest, audio_bytes: bytes, filename: str | None = None):
        session = self.get_session(session_id)
        settings = request.settings.dict(exclude_none=True)
        settings["request_id"] = request.request_id
        result = session.pipeline.transcribe(audio_bytes, request_settings=settings, filename=filename)
        result.session_id = session_id
        return result
