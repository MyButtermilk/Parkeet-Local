interface DesktopBridge {
  registerHotkey?: (hotkey: string) => Promise<void> | void;
  onHotkey?: (handler: () => void) => () => void;
}

declare global {
  interface Window {
    desktop?: DesktopBridge;
  }
}

export {};
