const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('kiosk', {
  isElectron: true,
  printReceipt: () => window.print(),
});
