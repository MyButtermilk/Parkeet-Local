from __future__ import annotations

"""Compatibility layer pointing to Pipecat's VAD wrapper."""

from app.pipecat.components import PipecatVAD as SileroVAD, SpeechSegment

__all__ = ["SileroVAD", "SpeechSegment"]
