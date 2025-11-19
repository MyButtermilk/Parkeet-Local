import { useCallback, useEffect, useRef, useState } from "react";

export interface UseAudioRecorderOptions {
  onLevel?: (level: number) => void;
  deviceId?: string;
}

export interface AudioRecorderControls {
  start: () => Promise<void>;
  stop: () => Promise<Blob>;
  reset: () => void;
  isRecording: boolean;
  duration: number;
}

export function useAudioRecorder({ onLevel, deviceId }: UseAudioRecorderOptions = {}): AudioRecorderControls {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>();
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const [duration, setDuration] = useState(0);
  const [isRecording, setIsRecording] = useState(false);

  const cleanup = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    analyserRef.current?.disconnect();
    audioContextRef.current?.close().catch(() => undefined);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    analyserRef.current = null;
    audioContextRef.current = null;
    streamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);
    setDuration(0);
  }, []);

  const visualize = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let index = 0; index < bufferLength; index += 1) {
        const value = (dataArray[index] - 128) / 128;
        sum += value * value;
      }
      const rms = Math.sqrt(sum / bufferLength);
      onLevel?.(Math.min(1, rms * 4));
      if (isRecording) {
        const now = performance.now();
        setDuration((now - startTimeRef.current) / 1000);
        rafRef.current = requestAnimationFrame(draw);
      }
    };

    rafRef.current = requestAnimationFrame(draw);
  }, [isRecording, onLevel]);

  const start = useCallback(async () => {
    if (isRecording) return;
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: deviceId ? { deviceId: { exact: deviceId } } : true,
      video: false
    });
    streamRef.current = stream;

    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyserRef.current = analyser;
    source.connect(analyser);

    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    chunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorder.start();
    startTimeRef.current = performance.now();
    setIsRecording(true);
    visualize();
  }, [isRecording, visualize]);

  const stop = useCallback(async () => {
    return new Promise<Blob>((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder) {
        cleanup();
        resolve(new Blob());
        return;
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        cleanup();
        resolve(blob);
      };

      recorder.stop();
    });
  }, [cleanup]);

  useEffect(() => () => cleanup(), [cleanup]);

  const reset = useCallback(() => {
    cleanup();
  }, [cleanup]);

  return {
    start,
    stop,
    reset,
    isRecording,
    duration
  };
}
