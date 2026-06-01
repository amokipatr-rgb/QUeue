const { app, BrowserWindow, shell } = require('electron');
const path = require('path');

const DISPLAY_URL = process.env.KIOSK_INDEX_URL
  || 'http://localhost:5000/';
const CRASH_RECOVERY_DELAY = 2000;

let mainWindow = null;
let isQuitting = false;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 680,
    center: true,
    title: 'Makerere University — Queue Management System',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      backgroundThrottling: false,
    },
  });

  mainWindow.loadURL(DISPLAY_URL).catch(() => {});

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.whenReady().then(() => {
  createWindow();
  console.log(`[App] Started — ${DISPLAY_URL}`);
});

app.on('activate', () => {
  if (!mainWindow) createWindow();
});
