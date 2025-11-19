from __future__ import annotations

"""Pipecat-facing settings shims.

These objects mirror the upstream Pipecat FastAPI backend configuration while
continuing to honor the existing ``Settings`` model and ``.env`` values used by
Parakeet Local. This keeps environment variables stable while letting Pipecat
code import familiar names.
"""

from pydantic import Field

from app.config import Settings as ParakeetSettings, get_settings as get_parakeet_settings


class PipecatSettings(ParakeetSettings):
    """Alias for the legacy Parakeet settings with Pipecat-friendly names."""

    api_prefix: str = Field(default="/api", description="Pipecat API prefix.")

    class Config(ParakeetSettings.Config):
        env_file = ParakeetSettings.Config.env_file
        env_nested_delimiter = ParakeetSettings.Config.env_nested_delimiter

    @property
    def asr_model_path(self):
        """Pipecat naming shim for the Parakeet model path."""

        return self.models.parakeet_model_path

    @property
    def tokenizer_path(self):
        return self.models.parakeet_tokenizer_path

    @property
    def vad_model_path(self):
        return self.models.silero_vad_path


def get_pipecat_settings() -> PipecatSettings:
    return PipecatSettings(**get_parakeet_settings().dict())
