# Parakeet Studio

Parakeet Studio is a local-first voice-to-text workstation built around the [`onnx-asr`](https://github.com/istupakov/onnx-asr) Parakeet v3 model paired with the latest Silero VAD ONNX detector. The experience combines a modern, glassmorphic interface inspired by the ElevenLabs UI system with a circular microphone visualizer for immersive real-time feedback.

## Features

- 🎙️ **Live microphone capture** with RMS-based circular waveform visualizer and instant level feedback.
- 📁 **File uploads** for WAV, MP3, OGG, and WebM audio, automatically trimmed via Silero VAD before transcription.
- ⚙️ **Rich settings** to control VAD, punctuation restoration, speaker diarization heuristics, and language hints.
- 🪶 **Parakeet v3 transcription pipeline** with cached ONNX Runtime sessions and optional local storage of processed audio.
- 🧠 **Silero VAD integration** with configurable thresholds to detect speech segments accurately.
- 🗂️ **Transcription timeline** with copy-to-clipboard actions and metadata for each session.

## Project layout

```
backend/   FastAPI application exposing transcription endpoints and ONNX-powered pipeline
frontend/  Vite + React (TypeScript) client with ElevenLabs UI-inspired styling
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The first run downloads the Parakeet v3 and Silero VAD ONNX models into `models/`. Adjust locations via environment variables defined in `app/config.py`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server defaults to `http://localhost:5173` and expects the backend at `http://localhost:8000` (configure via `VITE_API_URL`).

## Notes

- The ONNX model URLs can be overridden by placing the model files at the paths defined in `app/config.py` before starting the server.
- To deploy behind HTTPS or enable GPU inference, update the FastAPI settings and the ONNX Runtime provider list in `app/services/model_registry.py`.
