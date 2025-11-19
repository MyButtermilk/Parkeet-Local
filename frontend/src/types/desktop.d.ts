interface DesktopBridge {
  registerHotkey?: (hotkey: string) => Promise<void> | void;
  insertTextAtCursor?: (text: string) => Promise<boolean> | boolean;
  onHotkey?: (handler: () => void) => () => void;
}

declare global {
  interface Window {
    desktop?: DesktopBridge;
  }
}

export {};
