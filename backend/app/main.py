from __future__ import annotations

import json
import os
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import Settings, get_settings
from app.models.requests import TranscriptionRequest
from app.models.responses import TranscriptionResult
from app.models.pipecat import HotkeyEvent, HotkeyRegistration, PipecatOptions
from app.services.transcription_service import ParakeetTranscriptionService


def create_app(
    *,
    settings: Settings | None = None,
    service: ParakeetTranscriptionService | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Parakeet Local", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    service = service or ParakeetTranscriptionService(settings)
    pipecat_options = PipecatOptions(
        models=[
            {"id": "parakeet_v3", "label": "Parakeet v3 (ONNX)", "streaming": False},
            {"id": "parakeet_v3_stream", "label": "Parakeet v3 Streaming", "streaming": True},
        ],
        streaming_modes=["batch", "realtime"],
        input_devices=[],
        output_devices=[],
        default_hotkey="Ctrl+Shift+Space",
        upload_endpoint=f"{settings.api_prefix}/pipecat/transcriptions",
    )

    hotkey_state: HotkeyEvent | None = None
    hotkey_registered = False

    @app.get(f"{settings.api_prefix}/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(f"{settings.api_prefix}/pipecat/options", response_model=PipecatOptions)
    async def get_pipecat_options() -> PipecatOptions:
        """Expose Pipecat model/device defaults to the frontend."""

        return pipecat_options

    @app.post(f"{settings.api_prefix}/pipecat/events/hotkey", response_model=HotkeyRegistration)
    async def handle_hotkey(event: HotkeyEvent) -> HotkeyRegistration:
        nonlocal hotkey_state, hotkey_registered

        logger.info("Received hotkey event: {}", event)
        hotkey_state = event

        if event.state.lower() == "register":
            hotkey_registered = True
            pipecat_options.default_hotkey = event.hotkey
            return HotkeyRegistration(hotkey=event.hotkey, registered=True)

        if event.state.lower() in {"start", "stop", "toggle"}:
            if not hotkey_registered:
                return HotkeyRegistration(
                    hotkey=event.hotkey,
                    registered=False,
                    reason="Hotkey not registered yet",
                )

            return HotkeyRegistration(hotkey=event.hotkey, registered=True)

        return HotkeyRegistration(
            hotkey=event.hotkey,
            registered=False,
            reason=f"Unknown hotkey state '{event.state}'",
        )

    @app.post(f"{settings.api_prefix}/pipecat/transcriptions", response_model=TranscriptionResult)
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

    @app.post(f"{settings.api_prefix}/transcriptions", response_model=TranscriptionResult)
    async def transcribe_audio_legacy(
        file: UploadFile = File(...),
        payload: Annotated[str | None, Form()] = None,
    ) -> TranscriptionResult:
        return await transcribe_audio(file=file, payload=payload)

    return app


if os.getenv("PARAKEET_SKIP_APP_INIT") == "1":
    app = FastAPI(title="Parakeet Local", version="1.0.0")
else:
    app = create_app()
