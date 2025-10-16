from __future__ import annotations

import json
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import Settings, get_settings
from app.models.requests import TranscriptionRequest
from app.models.responses import TranscriptionResult
from app.services.transcription_service import ParakeetTranscriptionService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Parakeet Local", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    service = ParakeetTranscriptionService(settings)

    @app.get(f"{settings.api_prefix}/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(f"{settings.api_prefix}/transcriptions", response_model=TranscriptionResult)
    async def transcribe_audio(
        file: UploadFile = File(...),
        payload: Annotated[str | None, Form()] = None,
    ) -> TranscriptionResult:
        body = TranscriptionRequest()
        if payload:
            try:
                body = TranscriptionRequest(**json.loads(payload))
            except json.JSONDecodeError as exc:
                logger.warning("Failed to decode payload JSON: {}", exc)
        audio_bytes = await file.read()
        result = service.transcribe_bytes(audio_bytes, request=body, filename=file.filename)
        return result

    return app


app = create_app()
