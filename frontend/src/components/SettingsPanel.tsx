import { ChangeEvent } from "react";
import { Card, Input, Switch } from "./ui";

import type { AppSettings } from "../App";

interface SettingsPanelProps {
  settings: AppSettings;
  onChange: (settings: AppSettings) => void;
}

function SettingsPanel({ settings, onChange }: SettingsPanelProps) {
  const update = (partial: Partial<AppSettings>) => {
    onChange({ ...settings, ...partial });
  };

  const handleThreshold = (value: number[]) => {
    update({ vad_threshold: value[0] });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="glass-panel border-transparent p-6">
        <h3 className="text-lg font-semibold text-slate-100">Language & Punctuation</h3>
        <p className="mt-1 text-sm text-slate-400">
          Provide a language hint to bias the decoder and fine-tune punctuation reconstruction.
        </p>
        <div className="mt-6 space-y-4">
          <label className="flex flex-col gap-1 text-sm text-slate-300">
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">Language (optional)</span>
            <Input
              placeholder="e.g. en-US, fr-FR"
              value={settings.language ?? ""}
              onChange={(event: ChangeEvent<HTMLInputElement>) => update({ language: event.target.value })}
            />
          </label>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Automatic punctuation</p>
              <p className="text-xs text-slate-400">Restore punctuation and casing for easier reading.</p>
            </div>
            <Switch checked={settings.enable_punctuation} onCheckedChange={(value: boolean) => update({ enable_punctuation: value })} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Speaker diarization</p>
              <p className="text-xs text-slate-400">Tag segments with heuristic speaker labels.</p>
            </div>
            <Switch checked={settings.diarization} onCheckedChange={(value: boolean) => update({ diarization: value })} />
          </div>
        </div>
      </Card>

      <Card className="glass-panel border-transparent p-6">
        <h3 className="text-lg font-semibold text-slate-100">Voice Activity Detection</h3>
        <p className="mt-1 text-sm text-slate-400">
          Silero VAD trims silence and reduces background noise for faster inference.
        </p>
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Enable VAD</p>
              <p className="text-xs text-slate-400">Recommended for most recordings.</p>
            </div>
            <Switch checked={settings.enable_vad} onCheckedChange={(value: boolean) => update({ enable_vad: value })} />
          </div>
          <div>
            <div className="mb-3 flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-400">
              <span>Threshold</span>
              <span>{settings.vad_threshold?.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min={0.1}
              max={0.9}
              step={0.01}
              value={settings.vad_threshold ?? 0.45}
              onChange={(event) => handleThreshold([Number(event.target.value)])}
              className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-800 accent-indigo-400"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}

export default SettingsPanel;
