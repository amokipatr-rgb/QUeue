const { app, BrowserWindow, screen, powerSaveBlocker, globalShortcut } = require('electron');
const path = require('path');

const DISPLAY_URL = process.env.KIOSK_STUDENT_URL
  || 'https://queue-production-2a11.up.railway.app/student-token.html';
const RETRY_INTERVAL = 3000;
const CRASH_RECOVERY_DELAY = 2000;

let mainWindow = null;
let watchdogTimer = null;
let isQuitting = false;

let sleepBlockerId = null;
try {
  sleepBlockerId = powerSaveBlocker.start('prevent-display-sleep');
  console.log(`[StudentKiosk] Sleep blocker active: ${powerSaveBlocker.isStarted(sleepBlockerId)}`);
} catch (e) {
  console.warn('[StudentKiosk] Could not start sleep blocker');
}

function createKioskWindow() {
  const displays = screen.getAllDisplays();
  const targetDisplay = displays[0];
  const { x, y, width, height } = targetDisplay.bounds;

  mainWindow = new BrowserWindow({
    x, y, width, height,
    fullscreen: true,
    kiosk: true,
    frame: false,
    resizable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      backgroundThrottling: false,
    },
  });

  loadWithRetry();

  mainWindow.webContents.on('crashed', () => {
    console.error('[StudentKiosk] Renderer crashed — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.webContents.on('unresponsive', () => {
    console.warn('[StudentKiosk] Renderer unresponsive — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.on('closed', () => {
    if (!isQuitting) {
      console.log('[StudentKiosk] Window closed unexpectedly — recreating...');
      mainWindow = null;
      setTimeout(createKioskWindow, CRASH_RECOVERY_DELAY);
    }
  });
}

function loadWithRetry() {
  if (!mainWindow) return;

  mainWindow.loadURL(DISPLAY_URL).catch((err) => {
    console.warn(`[StudentKiosk] Load failed: ${err.message}. Retrying in ${RETRY_INTERVAL}ms...`);
    setTimeout(loadWithRetry, RETRY_INTERVAL);
  });
}

function restartKiosk() {
  if (mainWindow) {
    mainWindow.destroy();
    mainWindow = null;
  }
  createKioskWindow();
}

function startWatchdog() {
  watchdogTimer = setInterval(() => {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    mainWindow.webContents
      .executeJavaScript('true')
      .catch(() => {
        console.warn('[StudentKiosk] Watchdog: page unresponsive — restarting...');
        restartKiosk();
      });
  }, 30000);
}

app.on('before-quit', () => {
  isQuitting = true;
  if (watchdogTimer) {
    clearInterval(watchdogTimer);
    watchdogTimer = null;
  }
  if (sleepBlockerId && powerSaveBlocker.isStarted(sleepBlockerId)) {
    powerSaveBlocker.stop(sleepBlockerId);
  }
});

app.on('window-all-closed', () => {
  if (!isQuitting) {
    setTimeout(createKioskWindow, 1000);
  }
});

app.on('will-quit', (event) => {
  if (!isQuitting) {
    event.preventDefault();
  }
});

app.whenReady().then(() => {
  createKioskWindow();
  startWatchdog();
  console.log(`[StudentKiosk] Started — URL: ${DISPLAY_URL}`);
});

app.on('activate', () => {
  if (!mainWindow) createKioskWindow();
});
