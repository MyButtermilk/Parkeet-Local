const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktop", {
  registerHotkey: (hotkey) => ipcRenderer.invoke("desktop:register-hotkey", hotkey),
  onHotkey: (callback) => {
    ipcRenderer.on("desktop:hotkey", callback);
    return () => ipcRenderer.removeListener("desktop:hotkey", callback);
  }
});
