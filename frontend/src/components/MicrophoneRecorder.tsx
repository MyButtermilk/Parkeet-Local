import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from "react";
import { Button, Card } from "./ui";

import { TranscriptHistoryItem } from "../App";
import { useAudioRecorder } from "../hooks/useAudioRecorder";

interface MicrophoneRecorderProps {
  onLevelChange: (level: number) => void;
  onTranscribe: (
    blob: Blob,
    source: TranscriptHistoryItem["source"],
    filename?: string
  ) => Promise<TranscriptHistoryItem>;
  isProcessing: boolean;
  inputDeviceId?: string;
  onRecordingChange?: (state: boolean) => void;
}

export interface MicrophoneRecorderHandle {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  cancelRecording: () => void;
}

const MicrophoneRecorder = forwardRef<MicrophoneRecorderHandle, MicrophoneRecorderProps>(
  ({ onLevelChange, onTranscribe, isProcessing, inputDeviceId, onRecordingChange }, ref) => {
  const [error, setError] = useState<string | null>(null);
  const {
    start,
    stop,
    reset,
    isRecording,
    duration
  } = useAudioRecorder({
    onLevel: onLevelChange,
    deviceId: inputDeviceId
  });

  const handleStart = useCallback(async () => {
    try {
      setError(null);
      await start();
    } catch (err) {
      setError((err as Error).message ?? "Unable to access microphone");
    }
  }, [start]);

  const handleStop = useCallback(async () => {
    const blob = await stop();
    if (blob.size === 0) return;
    await onTranscribe(blob, "microphone", `mic-recording-${Date.now()}.webm`);
  }, [onTranscribe, stop]);

  const handleReset = useCallback(() => {
    reset();
    onLevelChange(0);
  }, [onLevelChange, reset]);

  useEffect(() => {
    onRecordingChange?.(isRecording);
  }, [isRecording, onRecordingChange]);

  useImperativeHandle(
    ref,
    () => ({
      startRecording: handleStart,
      stopRecording: async () => {
        await handleStop();
      },
      cancelRecording: handleReset
    }),
    [handleReset, handleStart, handleStop]
  );

  return (
    <Card className="glass-panel border-transparent p-6">
      <div className="flex flex-col gap-6">
        <div>
          <h3 className="text-xl font-semibold text-slate-100">Studio-grade capture</h3>
          <p className="mt-1 text-sm text-slate-400">
            Record high fidelity audio and let Parakeet v3 create transcripts in seconds. Voice Activity Detection ensures precise trims.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          {!isRecording ? (
            <Button
              onClick={handleStart}
              disabled={isProcessing}
              className="rounded-full bg-indigo-500/80 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-900/40 hover:bg-indigo-500"
            >
              {isProcessing ? "Processing…" : "Start Recording"}
            </Button>
          ) : (
            <>
              <Button
                onClick={handleStop}
                className="rounded-full bg-emerald-500/80 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-900/30 hover:bg-emerald-500"
              >
                Finish & Transcribe
              </Button>
              <Button
                onClick={handleReset}
                className="rounded-full bg-slate-800/60 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-700/60"
              >
                Cancel
              </Button>
            </>
          )}
        </div>

        <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between text-sm text-slate-300">
            <span className="font-medium uppercase tracking-[0.3em] text-indigo-200/80">
              {isRecording ? "Recording" : "Idle"}
            </span>
            <span>{new Date(duration * 1000).toISOString().substring(14, 19)}</span>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-sky-500 to-cyan-400 transition-all duration-200"
              style={{ width: `${Math.min(100, duration * 8)}%` }}
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}
      </div>
    </Card>
  );
});

export default MicrophoneRecorder;
