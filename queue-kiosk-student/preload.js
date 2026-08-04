const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('kiosk', {
  isElectron: true,
  printReceipt: () => ipcRenderer.send('print-receipt'),
});
