from __future__ import annotations

"""Legacy entry point redirected to Pipecat's pipeline."""

from app.pipecat.components import PipecatPipeline
from app.pipecat.settings import PipecatSettings
from app.pipecat.schemas import TranscriptionRequest, TranscriptionResult


class ParakeetTranscriptionService:
    def __init__(self, settings: PipecatSettings | None = None) -> None:
        self.pipeline = PipecatPipeline(settings)

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        request: TranscriptionRequest | None = None,
        filename: str | None = None,
    ) -> TranscriptionResult:
        request = request or TranscriptionRequest()
        settings = request.settings.dict(exclude_none=True)
        settings["request_id"] = request.request_id
        result = self.pipeline.transcribe(audio_bytes, request_settings=settings, filename=filename)
        result.session_id = request.session_id
        return result
