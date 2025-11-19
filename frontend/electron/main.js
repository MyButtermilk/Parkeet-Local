const { app, BrowserWindow, clipboard, globalShortcut, ipcMain, nativeImage, Tray } = require("electron");
const path = require("path");

let mainWindow = null;
let tray = null;
let robot;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: "#0b1221",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const startUrl = process.env.VITE_DEV_SERVER_URL || `file://${path.join(__dirname, "../dist/index.html")}`;
  void mainWindow.loadURL(startUrl);

  mainWindow.on("ready-to-show", () => {
    mainWindow?.show();
  });

  mainWindow.on("close", (event) => {
    if (process.platform === "win32") {
      event.preventDefault();
      mainWindow?.hide();
    }
  });
};

const registerHotkey = (accelerator) => {
  globalShortcut.unregisterAll();
  const success = globalShortcut.register(accelerator, () => {
    mainWindow?.webContents.send("desktop:hotkey");
  });
  return success;
};

const insertTextAtCursor = (text) => {
  clipboard.writeText(text);

  if (!robot) {
    try {
      // robotjs is optional; fall back to clipboard-only if unavailable.
      // eslint-disable-next-line global-require
      robot = require("robotjs");
    } catch (error) {
      console.warn("robotjs not installed; cannot simulate paste keystroke", error);
    }
  }

  if (robot) {
    const modifier = process.platform === "darwin" ? "command" : "control";
    try {
      robot.keyTap("v", modifier);
      return true;
    } catch (error) {
      console.warn("Failed to send paste keystroke via robotjs", error);
    }
  }

  const focused = BrowserWindow.getFocusedWindow();
  if (focused) {
    focused.webContents.pasteAndMatchStyle();
    return true;
  }

  return false;
};

const createTray = () => {
  const icon = nativeImage.createFromPath(path.join(__dirname, "icon.png"));
  tray = new Tray(icon);
  tray.setToolTip("Parakeet Transcription");
  tray.on("click", () => {
    if (!mainWindow) return;
    mainWindow.show();
    mainWindow.focus();
  });
};

app.whenReady().then(() => {
  createWindow();
  createTray();
  registerHotkey("CommandOrControl+Shift+Space");

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

ipcMain.handle("desktop:register-hotkey", (_event, hotkey) => {
  return registerHotkey(hotkey);
});

ipcMain.handle("desktop:insert-text", (_event, text) => {
  return insertTextAtCursor(text ?? "");
});
