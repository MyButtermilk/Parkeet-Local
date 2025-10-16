import { useEffect, useRef } from "react";

interface AudioVisualizerProps {
  level: number;
}

const BAR_COUNT = 64;

function AudioVisualizer({ level }: AudioVisualizerProps): JSX.Element {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    const radius = canvas.width / 2 - 12;

    context.clearRect(0, 0, canvas.width, canvas.height);
    context.save();
    context.translate(canvas.width / 2, canvas.height / 2);

    const maxBars = BAR_COUNT;
    for (let index = 0; index < maxBars; index += 1) {
      const progress = index / maxBars;
      const angle = progress * Math.PI * 2;
      const barHeight = 20 + level * 90 * Math.pow(Math.sin(progress * Math.PI), 1.5);
      const hue = 220 + level * 60 + progress * 60;

      context.strokeStyle = `hsla(${hue}, 90%, 65%, ${0.35 + level * 0.4})`;
      context.lineWidth = 4;
      context.beginPath();
      const inner = radius - 20;
      const outer = inner + barHeight;
      context.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner);
      context.lineTo(Math.cos(angle) * outer, Math.sin(angle) * outer);
      context.stroke();
    }

    context.restore();
  }, [level]);

  return (
    <div className="circular-visualizer">
      <canvas ref={canvasRef} width={220} height={220} />
      <div className="absolute inset-6 flex flex-col items-center justify-center rounded-full border border-indigo-500/30 bg-slate-900/50 shadow-lg shadow-indigo-900/30">
        <span className="text-sm uppercase tracking-[0.4em] text-indigo-200/80">Input</span>
        <span className="mt-2 text-2xl font-semibold text-slate-100">
          {(level * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}

export default AudioVisualizer;
