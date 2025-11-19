import { Button } from "./ui";
import type { TranscriptHistoryItem } from "../App";

interface HistoryToolbarProps {
  history: TranscriptHistoryItem[];
  onExport: () => void;
}

function HistoryToolbar({ history, onExport }: HistoryToolbarProps) {
  return (
    <div className="mt-4 flex items-center justify-between rounded-lg bg-slate-900/40 px-4 py-3 text-xs text-slate-300">
      <div className="space-y-1">
        <p className="font-semibold text-slate-100">{history.length} transcripts</p>
        <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Export keeps everything local</p>
      </div>
      <Button
        onClick={onExport}
        className="rounded-full bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-100 hover:bg-slate-700/80"
        disabled={history.length === 0}
      >
        Export JSON
      </Button>
    </div>
  );
}

export default HistoryToolbar;
