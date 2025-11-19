"""Pipecat-compatible backend wiring for Parakeet Local."""

from app.pipecat.api import router
from app.pipecat.settings import PipecatSettings, get_pipecat_settings

__all__ = ["router", "PipecatSettings", "get_pipecat_settings"]
