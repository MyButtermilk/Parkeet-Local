import { useCallback, useRef, useState } from "react";
import { Button, Card } from "./ui";

import { TranscriptHistoryItem } from "../App";

interface FileUploaderProps {
  onTranscribe: (
    blob: Blob,
    source: TranscriptHistoryItem["source"],
    filename?: string
  ) => Promise<TranscriptHistoryItem>;
  isProcessing: boolean;
}

const ACCEPTED_TYPES = ["audio/wav", "audio/mpeg", "audio/webm", "audio/ogg", "audio/x-wav"];

function FileUploader({ onTranscribe, isProcessing }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleChoose = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFiles = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      const file = fileList[0];
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError("Unsupported file type. Please upload WAV, MP3, OGG, or WEBM audio files.");
        return;
      }
      setError(null);
      setFileName(file.name);
      await onTranscribe(file, "file", file.name);
    },
    [onTranscribe]
  );

  const handleDrop = useCallback(
    async (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (event.dataTransfer?.files) {
        await handleFiles(event.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  return (
    <Card className="glass-panel border-transparent p-8 text-center">
      <div
        className="relative flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-indigo-500/40 bg-indigo-500/10 px-6 py-16 text-slate-200"
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500/20 text-2xl">
          ⬆️
        </div>
        <div>
          <p className="text-lg font-semibold">Drop audio here</p>
          <p className="mt-1 text-sm text-slate-300">
            WAV, MP3, OGG, or WEBM up to 2 hours. Silero VAD will automatically trim silence before transcription.
          </p>
        </div>
        <Button
          onClick={handleChoose}
          disabled={isProcessing}
          className="rounded-full bg-indigo-500/80 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 hover:bg-indigo-500"
        >
          {isProcessing ? "Uploading…" : "Browse files"}
        </Button>
        {fileName && (
          <p className="text-xs text-indigo-200/70">Last uploaded: {fileName}</p>
        )}
        {error && (
          <div className="mt-4 w-full rounded-lg border border-rose-500/50 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </div>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        hidden
        onChange={(event) => handleFiles(event.target.files)}
      />
    </Card>
  );
}

export default FileUploader;
