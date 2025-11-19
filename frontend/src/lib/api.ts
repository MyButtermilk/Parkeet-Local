import axios from "axios";

export interface DeviceOption {
  id: string;
  label: string;
  kind: "input" | "output";
}

export interface ModelOption {
  id: string;
  label: string;
  streaming: boolean;
}

export interface PipecatOptions {
  models: ModelOption[];
  streaming_modes: string[];
  input_devices: DeviceOption[];
  output_devices: DeviceOption[];
  default_hotkey: string;
  upload_endpoint: string;
}

export interface TranscriptionSettings {
  language?: string;
  model: string;
  streaming_mode: string;
  input_device?: string;
  output_device?: string;
  input_source?: string;
  enable_punctuation: boolean;
  enable_vad: boolean;
  vad_threshold?: number;
  diarization: boolean;
}

export interface TranscriptionRequestBody {
  request_id?: string;
  settings: TranscriptionSettings;
}

export interface TranscriptSegment {
  text: string;
  start: number;
  end: number;
  speaker?: string | null;
  confidence?: number | null;
}

export interface TranscriptionResponse {
  request_id?: string;
  created_at: string;
  text: string;
  duration: number;
  segments: TranscriptSegment[];
  settings_applied: Record<string, unknown>;
}

export interface HotkeyEvent {
  hotkey: string;
  state: string;
  request_id?: string;
}

export interface HotkeyRegistration {
  hotkey: string;
  registered: boolean;
  reason?: string | null;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
  timeout: 120000
});

export async function fetchPipecatOptions(): Promise<PipecatOptions> {
  const { data } = await api.get<PipecatOptions>("/pipecat/options");
  return data;
}

export async function uploadAudio(
  file: File | Blob,
  metadata: TranscriptionRequestBody,
  endpoint = "/pipecat/transcriptions"
): Promise<TranscriptionResponse> {
  const payload = new FormData();
  payload.append("file", file);
  payload.append("payload", JSON.stringify(metadata));
  const { data } = await api.post<TranscriptionResponse>(endpoint, payload, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function registerHotkey(event: HotkeyEvent): Promise<HotkeyRegistration> {
  const { data } = await api.post<HotkeyRegistration>("/pipecat/events/hotkey", event);
  return data;
}
