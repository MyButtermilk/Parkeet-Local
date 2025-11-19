from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from loguru import logger

from app.pipecat.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    TranscriptionRequest,
    TranscriptionResult,
)
from app.pipecat.session import SessionManager
from app.pipecat.settings import get_pipecat_settings

router = APIRouter()

settings = get_pipecat_settings()
session_manager = SessionManager(settings)


@router.get(f"{settings.api_prefix}/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post(f"{settings.api_prefix}/sessions", response_model=SessionCreateResponse)
async def create_session(payload: SessionCreateRequest | None = None) -> SessionCreateResponse:
    return session_manager.create_session(payload)


@router.post(f"{settings.api_prefix}/sessions/{{session_id}}/transcriptions", response_model=TranscriptionResult)
async def transcribe_audio(
    session_id: str,
    file: UploadFile = File(...),
    payload: Annotated[str | None, Form()] = None,
) -> TranscriptionResult:
    body = TranscriptionRequest(session_id=session_id)
    if payload:
        try:
            body = TranscriptionRequest(**json.loads(payload))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode payload JSON: {}", exc)
            body = TranscriptionRequest(session_id=session_id)

    if body.session_id and body.session_id != session_id:
        logger.warning(
            "Payload session_id %s does not match path session_id %s; using path value",
            body.session_id,
            session_id,
        )
    body.session_id = session_id
    audio_bytes = await file.read()
    result = session_manager.transcribe(session_id, body, audio_bytes, filename=file.filename)
    return result


@router.post(f"{settings.api_prefix}/transcriptions", response_model=TranscriptionResult)
async def transcribe_with_default_session(
    file: UploadFile = File(...),
    payload: Annotated[str | None, Form()] = None,
) -> TranscriptionResult:
    default_session = session_manager.create_session(SessionCreateRequest(session_id="default"))
    return await transcribe_audio(default_session.session_id, file=file, payload=payload)
