import { useCallback } from "react";
import { Badge, Button } from "./ui";

import type { TranscriptHistoryItem } from "../App";

interface TranscriptListProps {
  history: TranscriptHistoryItem[];
  isProcessing: boolean;
}

function TranscriptList({ history, isProcessing }: TranscriptListProps) {
  const handleCopy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
  }, []);

  if (history.length === 0) {
    return (
      <div className="mt-6 rounded-xl border border-dashed border-slate-700/60 bg-slate-900/20 p-6 text-sm text-slate-400">
        No transcripts yet. Record audio or upload a file to see your transcription timeline.
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-4">
      {history.map((item) => (
        <div key={item.request_id} className="rounded-xl border border-slate-700/50 bg-slate-900/30 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs uppercase tracking-[0.3em] text-slate-400">
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <Badge
              className={
                item.source === "microphone"
                  ? "bg-indigo-500/20 text-indigo-200"
                  : "bg-sky-500/20 text-sky-200"
              }
            >
              {item.source === "microphone" ? "Microphone" : item.filename ?? "Upload"}
            </Badge>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-100">{item.text}</p>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
            <span>
              Duration: {item.duration.toFixed(1)}s · Segments: {item.segments.length}
            </span>
            <Button
              disabled={isProcessing}
              onClick={() => handleCopy(item.text)}
              className="rounded-full bg-slate-800/60 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700/60"
            >
              Copy transcript
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default TranscriptList;
