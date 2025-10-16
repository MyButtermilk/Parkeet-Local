from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, BaseSettings, Field


class ModelPaths(BaseModel):
    """Configuration for model and resource paths."""

    parakeet_model_path: Path = Field(
        default=Path("models/parakeet_v3/model.onnx"),
        description="Path to the Parakeet v3 ONNX model file.",
    )
    parakeet_tokenizer_path: Path = Field(
        default=Path("models/parakeet_v3/tokenizer.json"),
        description="Path to the tokenizer configuration for the Parakeet model.",
    )
    silero_vad_path: Path = Field(
        default=Path("models/silero_vad/silero_vad.onnx"),
        description="Path to the Silero VAD ONNX model file.",
    )


class Settings(BaseSettings):
    """Application configuration."""

    api_prefix: str = Field(default="/api", description="Base API prefix for all routes.")
    storage_dir: Path = Field(
        default=Path("data/uploads"),
        description="Directory where uploaded audio files will be stored.",
    )
    models: ModelPaths = Field(default_factory=ModelPaths)
    sample_rate: int = Field(default=16000, description="Target sample rate for ASR input.")
    max_segment_seconds: float = Field(
        default=30.0,
        description="Maximum duration for each segment processed by the ASR.",
    )
    vad_threshold: float = Field(
        default=0.4,
        description="Default probability threshold for the Silero VAD model.",
    )
    vad_min_speech_seconds: float = Field(
        default=0.25,
        description="Minimum speech duration that will be considered a valid speech chunk.",
    )
    vad_min_silence_seconds: float = Field(
        default=0.5,
        description="Minimum silence duration required to split speech segments.",
    )

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of application settings."""

    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.models.parakeet_model_path.parent.mkdir(parents=True, exist_ok=True)
    settings.models.silero_vad_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
