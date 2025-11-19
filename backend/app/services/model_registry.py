from __future__ import annotations

"""Backward-compatible shim for Pipecat model registry wiring."""

from app.pipecat.components import PipecatModelRegistry
from app.pipecat.settings import PipecatSettings

_registry: PipecatModelRegistry | None = None


def get_registry(settings: PipecatSettings | None = None) -> PipecatModelRegistry:
    global _registry
    if _registry is None:
        _registry = PipecatModelRegistry(settings=settings)
    return _registry
