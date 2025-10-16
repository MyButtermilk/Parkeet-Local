interface EnsureWavOptions {
  originalName?: string;
}

function toFileName(base: string, extension: string): string {
  const sanitized = base.replace(/[^a-z0-9-_]+/gi, "-").replace(/-+/g, "-");
  return `${sanitized || "audio"}.${extension}`;
}

function stripExtension(name: string | undefined): string {
  if (!name) return "audio";
  const lastDot = name.lastIndexOf(".");
  if (lastDot === -1) return name;
  return name.slice(0, lastDot);
}

function writeString(view: DataView, offset: number, text: string): void {
  for (let index = 0; index < text.length; index += 1) {
    view.setUint8(offset + index, text.charCodeAt(index));
  }
}

function floatTo16BitPCM(view: DataView, offset: number, input: Float32Array): void {
  for (let index = 0; index < input.length; index += 1, offset += 2) {
    const sample = Math.max(-1, Math.min(1, input[index]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }
}

function interleave(buffer: AudioBuffer): Float32Array {
  const { numberOfChannels, length } = buffer;
  if (numberOfChannels === 1) {
    return buffer.getChannelData(0).slice();
  }
  const result = new Float32Array(length * numberOfChannels);
  for (let channel = 0; channel < numberOfChannels; channel += 1) {
    const channelData = buffer.getChannelData(channel);
    for (let index = 0; index < length; index += 1) {
      result[index * numberOfChannels + channel] = channelData[index];
    }
  }
  return result;
}

function encodeWavBuffer(buffer: AudioBuffer): ArrayBuffer {
  const sampleRate = buffer.sampleRate;
  const channels = buffer.numberOfChannels;
  const samples = interleave(buffer);
  const bitsPerSample = 16;
  const blockAlign = (channels * bitsPerSample) / 8;
  const byteRate = sampleRate * blockAlign;
  const dataSize = samples.length * 2;
  const bufferSize = 44 + dataSize;
  const arrayBuffer = new ArrayBuffer(bufferSize);
  const view = new DataView(arrayBuffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);
  floatTo16BitPCM(view, 44, samples);

  return arrayBuffer;
}

async function transcodeToWav(blob: Blob, fileNameBase: string): Promise<File> {
  const context = new AudioContext();
  try {
    const buffer = await context.decodeAudioData(await blob.arrayBuffer());
    const wavBuffer = encodeWavBuffer(buffer);
    return new File([wavBuffer], toFileName(fileNameBase, "wav"), { type: "audio/wav" });
  } finally {
    await context.close().catch(() => undefined);
  }
}

export async function ensureWavFile(
  source: Blob,
  options: EnsureWavOptions = {}
): Promise<File> {
  const originalBase = stripExtension(options.originalName);
  const wavLike = ["audio/wav", "audio/x-wav", "audio/wave"];
  if (source instanceof File && wavLike.includes(source.type)) {
    return source;
  }
  if (wavLike.includes(source.type)) {
    return new File([source], toFileName(originalBase, "wav"), { type: "audio/wav" });
  }
  return transcodeToWav(source, originalBase);
}

