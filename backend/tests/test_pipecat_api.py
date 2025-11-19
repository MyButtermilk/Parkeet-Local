from __future__ import annotations

import asyncio
import io
import json

from starlette.datastructures import UploadFile

from app.pipecat import api
from app.pipecat.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    TranscriptionRequest,
    TranscriptionResult,
)


class DummySessionManager:
    def __init__(self, session_id: str = "session-1") -> None:
        self.session_id = session_id
        self.created_payloads: list[SessionCreateRequest | None] = []
        self.transcriptions: list[tuple[str, TranscriptionRequest, bytes, str | None]] = []

    def create_session(self, payload: SessionCreateRequest | None = None) -> SessionCreateResponse:
        self.created_payloads.append(payload)
        return SessionCreateResponse(session_id=self.session_id)

    def transcribe(
        self, session_id: str, request: TranscriptionRequest, audio_bytes: bytes, filename: str | None = None
    ) -> TranscriptionResult:
        self.transcriptions.append((session_id, request, audio_bytes, filename))
        return TranscriptionResult(
            session_id=session_id,
            request_id=request.request_id,
            text="hello",
            duration=0.1,
            segments=[],
            settings_applied={"enable_punctuation": request.settings.enable_punctuation},
        )


def test_healthcheck_returns_ok(monkeypatch):
    api.session_manager = DummySessionManager()

    result = asyncio.run(api.healthcheck())

    assert result == {"status": "ok"}


def test_create_session_uses_manager(monkeypatch):
    dummy_manager = DummySessionManager(session_id="abc123")
    api.session_manager = dummy_manager

    response = asyncio.run(api.create_session(SessionCreateRequest(session_id="abc123")))

    assert response.session_id == "abc123"
    assert dummy_manager.created_payloads[0].session_id == "abc123"


def test_transcribe_enforces_path_session_id(monkeypatch):
    dummy_manager = DummySessionManager(session_id="path-id")
    api.session_manager = dummy_manager
    payload = json.dumps({"request_id": "req-1", "session_id": "payload-id", "settings": {"enable_vad": False}})
    upload = UploadFile(filename="sample.wav", file=io.BytesIO(b"audio-bytes"))

    response = asyncio.run(api.transcribe_audio("path-id", file=upload, payload=payload))

    assert response.session_id == "path-id"
    assert dummy_manager.transcriptions, "Transcription should be called"
    session_id, request, audio_bytes, filename = dummy_manager.transcriptions[0]
    assert session_id == "path-id"
    assert request.session_id == "path-id"
    assert request.request_id == "req-1"
    assert audio_bytes == b"audio-bytes"
    assert filename == "sample.wav"


def test_default_transcription_creates_session(monkeypatch):
    dummy_manager = DummySessionManager(session_id="generated")
    api.session_manager = dummy_manager
    upload = UploadFile(filename="voice.wav", file=io.BytesIO(b"audio"))

    response = asyncio.run(api.transcribe_with_default_session(file=upload))

    assert response.session_id == "generated"
    assert dummy_manager.created_payloads, "Default session should be created"
    assert dummy_manager.transcriptions, "Default session should be used for transcription"
    session_id, request, *_ = dummy_manager.transcriptions[0]
    assert session_id == "generated"
    assert request.session_id == "generated"
