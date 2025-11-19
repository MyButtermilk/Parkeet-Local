import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as Tabs from "./components/Tabs";
import { Badge, Button, Card } from "./components/ui";

import type {
  TranscriptionRequestBody,
  TranscriptionResponse,
  TranscriptionSettings,
  PipecatOptions,
  HotkeyRegistration
} from "./lib/api";
import { fetchPipecatOptions, registerHotkey, uploadAudio } from "./lib/api";
import AudioVisualizer from "./components/AudioVisualizer";
import MicrophoneRecorder, { MicrophoneRecorderHandle } from "./components/MicrophoneRecorder";
import FileUploader from "./components/FileUploader";
import SettingsPanel from "./components/SettingsPanel";
import TranscriptList from "./components/TranscriptList";
import { ensureWavFile } from "./utils/audio";
import BackgroundStatus from "./components/BackgroundStatus";
import HistoryToolbar from "./components/HistoryToolbar";

export type AppSettings = TranscriptionSettings;

const defaultSettings: AppSettings = {
  model: "parakeet_v3",
  streaming_mode: "batch",
  input_device: undefined,
  output_device: undefined,
  input_source: "microphone",
  language: "",
  enable_punctuation: true,
  enable_vad: true,
  vad_threshold: 0.45,
  diarization: false
};

export interface TranscriptHistoryItem extends TranscriptionResponse {
  source: "microphone" | "file";
  filename?: string;
}

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>("microphone");
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [isProcessing, setIsProcessing] = useState(false);
  const [history, setHistory] = useState<TranscriptHistoryItem[]>([]);
  const [liveLevel, setLiveLevel] = useState(0);
  const [options, setOptions] = useState<PipecatOptions | null>(null);
  const [hotkeyRegistration, setHotkeyRegistration] = useState<HotkeyRegistration | null>(null);
  const [statusMessage, setStatusMessage] = useState("Idle");
  const [isRecording, setIsRecording] = useState(false);
  const [insertAfterHotkey, setInsertAfterHotkey] = useState(false);
  const recorderRef = useRef<MicrophoneRecorderHandle | null>(null);

  useEffect(() => {
    fetchPipecatOptions()
      .then((data) => {
        setOptions(data);
        setSettings((prev) => ({
          ...prev,
          model: prev.model || data.models[0]?.id || "parakeet_v3",
          streaming_mode: prev.streaming_mode || data.streaming_modes[0] || "batch",
          input_device: prev.input_device ?? data.input_devices[0]?.id,
          output_device: prev.output_device ?? data.output_devices[0]?.id
        }));
        setHotkeyRegistration({ hotkey: data.default_hotkey, registered: false, reason: null });
      })
      .catch(() => {
        setOptions(null);
      });
  }, []);

  const metadata = useMemo<TranscriptionRequestBody>(
    () => ({
      settings: {
        ...settings,
        language: settings.language || undefined
      }
    }),
    [settings]
  );

  const insertTranscriptText = useCallback(async (text: string) => {
    if (!text) return;

    setStatusMessage("Inserting transcript…");
    try {
      const inserted = await window.desktop?.insertTextAtCursor?.(text);
      if (inserted) {
        setStatusMessage("Transcript inserted via hotkey");
        return;
      }
    } catch (error) {
      console.warn("Failed to insert via desktop bridge", error);
    }

    try {
      await navigator.clipboard.writeText(text);
      setStatusMessage("Transcript copied to clipboard");
    } catch (error) {
      console.warn("Failed to copy transcript to clipboard", error);
      setStatusMessage("Unable to insert transcript automatically");
    }
  }, []);

  const handleTranscription = async (
    blob: Blob,
    source: TranscriptHistoryItem["source"],
    filename?: string
  ) => {
    setIsProcessing(true);
    try {
      const prepared = await ensureWavFile(blob, { originalName: filename });
      const response = await uploadAudio(
        prepared,
        {
          ...metadata,
          settings: {
            ...metadata.settings,
            input_source: source
          }
        },
        options?.upload_endpoint ?? "/pipecat/transcriptions"
      );
      const transcript: TranscriptHistoryItem = {
        ...response,
        source,
        filename
      };
      setHistory((prev) => [transcript, ...prev]);
      if (source === "microphone" && insertAfterHotkey) {
        await insertTranscriptText(response.text);
        setInsertAfterHotkey(false);
      }
      return transcript;
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHotkeyRegister = async () => {
    const hotkeyLabel = hotkeyRegistration?.hotkey || options?.default_hotkey || "Ctrl+Shift+Space";
    const registration = await registerHotkey({ hotkey: hotkeyLabel, state: "register" });
    setHotkeyRegistration(registration);
    await window.desktop?.registerHotkey?.(hotkeyLabel);
    setStatusMessage(`Hotkey ${hotkeyLabel} ready`);
  };

  const handleHotkeyToggle = useMemo(
    () => async () => {
      const hotkeyLabel = hotkeyRegistration?.hotkey || options?.default_hotkey || "Ctrl+Shift+Space";
      await registerHotkey({
        hotkey: hotkeyLabel,
        state: isRecording ? "stop" : "start"
      });
      if (isRecording) {
        setStatusMessage("Stopping capture from hotkey");
        await recorderRef.current?.stopRecording();
      } else {
        setStatusMessage("Hotkey toggled recording");
        setInsertAfterHotkey(true);
        await recorderRef.current?.startRecording();
      }
    },
    [hotkeyRegistration?.hotkey, isRecording, options?.default_hotkey]
  );

  useEffect(() => {
    const unsubscribeDesktop = window.desktop?.onHotkey?.(() => {
      void handleHotkeyToggle();
    });

    const fallback = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.code === "Space") {
        event.preventDefault();
        void handleHotkeyToggle();
      }
    };

    window.addEventListener("keydown", fallback);
    return () => {
      unsubscribeDesktop?.();
      window.removeEventListener("keydown", fallback);
    };
  }, [handleHotkeyToggle]);

  const handleExportHistory = () => {
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `parakeet-transcripts-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen px-6 pb-16 pt-8 sm:px-10 lg:px-16">
      <header className="mx-auto flex max-w-6xl items-center justify-between pb-8">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500/30 text-lg font-semibold text-indigo-200 shadow-glass">
              🐦
            </span>
            <h1 className="text-2xl font-semibold text-slate-100 sm:text-3xl">Parakeet Studio</h1>
            <Badge className="bg-indigo-500/20 text-indigo-200">Parakeet v3</Badge>
          </div>
          <p className="max-w-2xl text-sm text-slate-300 sm:text-base">
            Capture pristine voice notes, interviews, and podcasts with streaming-quality transcription powered by Parakeet v3 and Silero VAD.
          </p>
        </div>
        <Badge className="bg-sky-500/20 text-sky-200">Local-first</Badge>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="glass-panel border-transparent p-0">
          <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
            <div className="flex items-center justify-between border-b border-slate-700/50 px-6 py-4">
              <Tabs.List className="flex gap-3">
                <Tabs.Trigger value="microphone" asChild>
                  <Button
                    className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                      activeTab === "microphone"
                        ? "bg-indigo-500/30 text-indigo-100 shadow-glass"
                        : "bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
                    }`}
                  >
                    🎙️ Live Mic
                  </Button>
                </Tabs.Trigger>
                <Tabs.Trigger value="file" asChild>
                  <Button
                    className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                      activeTab === "file"
                        ? "bg-indigo-500/30 text-indigo-100 shadow-glass"
                        : "bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
                    }`}
                  >
                    📁 File Upload
                  </Button>
                </Tabs.Trigger>
                <Tabs.Trigger value="settings" asChild>
                  <Button
                    className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                      activeTab === "settings"
                        ? "bg-indigo-500/30 text-indigo-100 shadow-glass"
                        : "bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
                    }`}
                  >
                    ⚙️ Settings
                  </Button>
                </Tabs.Trigger>
              </Tabs.List>
              <div className="hidden text-xs uppercase tracking-[0.3em] text-slate-400 sm:block">
                {isProcessing ? "Transcribing…" : "Ready"}
              </div>
            </div>

            <Tabs.Content value="microphone">
              <div className="grid gap-8 px-6 py-8 lg:grid-cols-[260px_1fr]">
                <Card className="glass-panel flex flex-col items-center gap-6 border-transparent p-6 text-center">
                  <AudioVisualizer level={liveLevel} />
                  <p className="text-sm text-slate-300">
                    Speak clearly and stay within a consistent distance from your microphone for best results.
                  </p>
                </Card>
                <MicrophoneRecorder
                  ref={recorderRef}
                  inputDeviceId={settings.input_device}
                  onLevelChange={setLiveLevel}
                  onTranscribe={handleTranscription}
                  isProcessing={isProcessing}
                  onRecordingChange={setIsRecording}
                  onCancel={() => {
                    setInsertAfterHotkey(false);
                    setStatusMessage("Idle");
                  }}
                />
              </div>
            </Tabs.Content>

            <Tabs.Content value="file">
              <div className="px-6 py-8">
                <FileUploader onTranscribe={handleTranscription} isProcessing={isProcessing} />
              </div>
            </Tabs.Content>

            <Tabs.Content value="settings">
              <div className="px-6 py-8">
                <SettingsPanel settings={settings} onChange={setSettings} options={options} />
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </Card>

        <aside className="space-y-6">
          <BackgroundStatus
            hotkey={hotkeyRegistration?.hotkey || options?.default_hotkey || "Ctrl+Shift+Space"}
            registered={Boolean(hotkeyRegistration?.registered)}
            status={statusMessage}
            lastEvent={history[0]?.created_at}
            onRegister={handleHotkeyRegister}
          />
          <Card className="glass-panel border-transparent p-6">
            <h2 className="text-lg font-semibold text-slate-100">Transcription History</h2>
            <p className="text-sm text-slate-400">
              All transcripts are processed locally and remain on your machine until you explicitly export them.
            </p>
            <HistoryToolbar history={history} onExport={handleExportHistory} />
            <TranscriptList history={history} isProcessing={isProcessing} />
          </Card>
        </aside>
      </div>
    </div>
  );
}

export default App;
