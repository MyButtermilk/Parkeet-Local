import { Badge, Button, Card } from "./ui";

interface BackgroundStatusProps {
  hotkey: string;
  registered: boolean;
  status: string;
  lastEvent?: string;
  onRegister?: () => void | Promise<void>;
}

function BackgroundStatus({ hotkey, registered, status, lastEvent, onRegister }: BackgroundStatusProps) {
  return (
    <Card className="glass-panel border-transparent p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Background Agent</h2>
          <p className="text-sm text-slate-400">Runs quietly in the system tray and wakes up via your global hotkey.</p>
        </div>
        <Badge className={registered ? "bg-emerald-500/20 text-emerald-200" : "bg-amber-500/20 text-amber-200"}>
          {registered ? "Armed" : "Inactive"}
        </Badge>
      </div>
      <div className="mt-4 space-y-3 text-sm text-slate-300">
        <div className="flex items-center justify-between">
          <span className="uppercase tracking-[0.25em] text-xs text-slate-400">Hotkey</span>
          <span className="rounded-full bg-slate-800 px-3 py-1 font-semibold text-slate-100">{hotkey}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="uppercase tracking-[0.25em] text-xs text-slate-400">Status</span>
          <span className="text-slate-200">{status}</span>
        </div>
        {lastEvent && (
          <div className="flex items-center justify-between">
            <span className="uppercase tracking-[0.25em] text-xs text-slate-400">Last Event</span>
            <span className="text-slate-200">{new Date(lastEvent).toLocaleString()}</span>
          </div>
        )}
      </div>
      <div className="mt-4 flex justify-end">
        <Button
          onClick={() => onRegister?.()}
          className="rounded-full bg-indigo-500/80 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500"
        >
          {registered ? "Refresh hotkey" : "Register hotkey"}
        </Button>
      </div>
    </Card>
  );
}

export default BackgroundStatus;
