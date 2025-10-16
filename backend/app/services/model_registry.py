from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict
import onnxruntime as ort
import requests
from loguru import logger

from app.config import Settings, get_settings

PARAKEET_MODEL_URL = (
    "https://huggingface.co/onnx-community/parakeet-ctc-v3/resolve/main/model.onnx?download=1"
)
PARAKEET_TOKENIZER_URL = (
    "https://huggingface.co/onnx-community/parakeet-ctc-v3/resolve/main/tokenizer.json?download=1"
)
SILERO_VAD_URL = "https://huggingface.co/snakers4/silero-vad/resolve/main/models/silero_vad.onnx?download=1"


class ModelRegistry:
    """Handle model downloading and lazy loading for the ASR pipeline."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._sessions: Dict[str, ort.InferenceSession] = {}
        self._tokenizer: Dict[str, Any] | None = None

    def ensure_resources(self) -> None:
        """Ensure that all required model files are available locally."""

        self._download_if_missing(
            self.settings.models.parakeet_model_path, PARAKEET_MODEL_URL
        )
        self._download_if_missing(
            self.settings.models.parakeet_tokenizer_path, PARAKEET_TOKENIZER_URL
        )
        self._download_if_missing(self.settings.models.silero_vad_path, SILERO_VAD_URL)

    def get_asr_session(self) -> ort.InferenceSession:
        """Return the cached ASR ONNX session."""

        if "parakeet" not in self._sessions:
            self.ensure_resources()
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._sessions["parakeet"] = ort.InferenceSession(
                str(self.settings.models.parakeet_model_path),
                providers=providers,
            )
            logger.info("Loaded Parakeet v3 ASR model from {}", self.settings.models.parakeet_model_path)
        return self._sessions["parakeet"]

    def get_vad_session(self) -> ort.InferenceSession:
        """Return the cached Silero VAD session."""

        if "silero_vad" not in self._sessions:
            self.ensure_resources()
            providers = ["CPUExecutionProvider"]
            self._sessions["silero_vad"] = ort.InferenceSession(
                str(self.settings.models.silero_vad_path),
                providers=providers,
            )
            logger.info("Loaded Silero VAD model from {}", self.settings.models.silero_vad_path)
        return self._sessions["silero_vad"]

    def get_tokenizer(self) -> Dict[str, Any]:
        """Return the tokenizer metadata for the ASR model."""

        if self._tokenizer is None:
            self.ensure_resources()
            with self.settings.models.parakeet_tokenizer_path.open("r", encoding="utf-8") as handle:
                self._tokenizer = json.load(handle)
        return self._tokenizer

    def _download_if_missing(self, path: Path, url: str) -> None:
        if path.exists():
            return

        logger.info("Downloading %s", url)
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        with path.open("wb") as destination:
            shutil.copyfileobj(response.raw, destination)
        logger.info("Downloaded resource to %s", path)


_registry: ModelRegistry | None = None


def get_registry(settings: Settings | None = None) -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry(settings=settings)
    return _registry
