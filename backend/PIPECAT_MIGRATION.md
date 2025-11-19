# Pipecat backend alignment

The FastAPI backend now mirrors Pipecat's session-aware routing. Existing `.env`
values remain compatible through the `PipecatSettings` shim, which reuses the
legacy `Settings` model while exposing `asr_model_path`, `tokenizer_path`, and
`vad_model_path` aliases expected by Pipecat components.

## Routing changes
- `POST /api/sessions` creates or upserts a Pipecat session (you can provide
  your own `session_id`).
- `POST /api/sessions/{session_id}/transcriptions` sends audio for that session.
- `POST /api/transcriptions` remains as a compatibility shim that routes through
  a default session.

## Settings surface
- The existing environment variables continue to work. Paths defined under
  `models__parakeet_model_path`, `models__parakeet_tokenizer_path`, and
  `models__silero_vad_path` are now surfaced to Pipecat as
  `asr_model_path`, `tokenizer_path`, and `vad_model_path`.
- API prefix remains driven by `API_PREFIX` (`/api` by default) to match
  Pipecat's defaults.

No data migrations are required; model downloads remain in the same locations.
