import asyncio
import os
import sys
import unittest
from pathlib import Path

os.environ["PARAKEET_SKIP_APP_INIT"] = "1"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import create_app
from app.models.pipecat import HotkeyEvent, PipecatOptions


class _StubTranscriptionService:
    """Lightweight stand-in to avoid heavy model initialization during tests."""

    def transcribe_bytes(self, *args, **kwargs):  # pragma: no cover - not used in these tests
        raise NotImplementedError

class PipecatEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = create_app(service=_StubTranscriptionService())

    async def test_pipecat_options_exposes_defaults(self):
        route = next(r for r in self.app.routes if getattr(r, "path", None) == "/api/pipecat/options")

        result: PipecatOptions = await asyncio.ensure_future(route.endpoint())

        self.assertGreaterEqual(len(result.models), 1)
        self.assertEqual(result.default_hotkey, "Ctrl+Shift+Space")
        self.assertEqual(result.upload_endpoint, "/api/pipecat/transcriptions")

    async def test_hotkey_registration_acknowledged(self):
        route = next(
            r
            for r in self.app.routes
            if getattr(r, "path", None) == "/api/pipecat/events/hotkey"
        )

        result = await asyncio.ensure_future(
            route.endpoint(HotkeyEvent(hotkey="Ctrl+Shift+Space", state="register"))
        )

        self.assertTrue(result.registered)
        self.assertEqual(result.hotkey, "Ctrl+Shift+Space")
