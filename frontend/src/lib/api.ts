import axios from "axios";

export interface TranscriptionSettings {
  language?: string;
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

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
  timeout: 120000
});

export async function uploadAudio(
  file: File | Blob,
  metadata: TranscriptionRequestBody
): Promise<TranscriptionResponse> {
  const payload = new FormData();
  payload.append("file", file);
  payload.append("payload", JSON.stringify(metadata));
  const { data } = await api.post<TranscriptionResponse>("/transcriptions", payload, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}
