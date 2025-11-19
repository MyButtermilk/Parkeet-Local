import io
import json
import os
import sys
import unittest
from pathlib import Path

from starlette.datastructures import UploadFile

os.environ["PARAKEET_SKIP_APP_INIT"] = "1"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import create_app
from app.models.pipecat import HotkeyEvent, PipecatOptions
from app.models.responses import TranscriptionResult


class _StubTranscriptionService:
    """Lightweight stand-in to avoid heavy model initialization during tests."""

    def __init__(self):
        self.calls: list[tuple[bytes, dict, str]] = []

    def transcribe_bytes(self, audio_bytes: bytes, request, filename: str):
        self.calls.append((audio_bytes, request.dict(), filename))
        return TranscriptionResult(
            text="Stub transcript",
            duration=1.0,
            segments=[],
            settings_applied={"source": request.settings.input_source},
        )


class PipecatEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = _StubTranscriptionService()
        self.app = create_app(service=self.service)

    async def test_pipecat_options_exposes_defaults(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/options")

        result: PipecatOptions = await route.endpoint()

        self.assertGreaterEqual(len(result.models), 1)
        self.assertEqual(result.default_hotkey, "Ctrl+Shift+Space")
        self.assertEqual(result.upload_endpoint, "/api/pipecat/transcriptions")

    async def test_hotkey_registration_acknowledged(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/events/hotkey")

        result = await route.endpoint(HotkeyEvent(hotkey="Ctrl+Shift+Space", state="register"))

        self.assertTrue(result.registered)
        self.assertEqual(result.hotkey, "Ctrl+Shift+Space")

    async def test_hotkey_start_requires_registration(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/events/hotkey")

        result = await route.endpoint(HotkeyEvent(hotkey="Ctrl+Shift+Space", state="start"))

        self.assertFalse(result.registered)
        self.assertIn("not registered", (result.reason or "").lower())

    async def test_hotkey_registration_updates_default_and_allows_toggle(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/events/hotkey")
        options_route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/options")

        await route.endpoint(HotkeyEvent(hotkey="Alt+Shift+T", state="register"))

        toggle_response = await route.endpoint(HotkeyEvent(hotkey="Alt+Shift+T", state="start"))
        options_response: PipecatOptions = await options_route.endpoint()

        self.assertTrue(toggle_response.registered)
        self.assertEqual(options_response.default_hotkey, "Alt+Shift+T")

    async def test_unknown_hotkey_state_returns_reason(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/events/hotkey")

        result = await route.endpoint(HotkeyEvent(hotkey="Ctrl+Shift+Space", state="invalid"))

        self.assertFalse(result.registered)
        self.assertIn("unknown hotkey state", (result.reason or "").lower())

    async def test_transcription_endpoint_forwards_payload_to_service(self):
        payload = {"settings": {"input_source": "microphone", "model": "parakeet_v3"}}
        audio_file = UploadFile(filename="audio.wav", file=io.BytesIO(b"123"))
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/transcriptions")

        response: TranscriptionResult = await route.endpoint(file=audio_file, payload=json.dumps(payload))

        self.assertEqual(response.text, "Stub transcript")
        self.assertEqual(len(self.service.calls), 1)
        audio_bytes, request_body, filename = self.service.calls[0]
        self.assertEqual(audio_bytes, b"123")
        self.assertEqual(request_body["settings"]["input_source"], "microphone")
        self.assertEqual(filename, "audio.wav")
