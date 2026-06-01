const { app, BrowserWindow, screen, powerSaveBlocker, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');

// ── Configuration ──
const DISPLAY_URL = process.env.KIOSK_URL
  || 'https://queue-production-2a11.up.railway.app/public-display.html';
const RETRY_INTERVAL = 3000;   // ms between connection retries
const CRASH_RECOVERY_DELAY = 2000;
const CURSOR_HIDE_DELAY = 3000;

let mainWindow = null;
let watchdogTimer = null;
let isQuitting = false;

// ── Prevent system sleep ──
const sleepBlockerId = powerSaveBlocker.start('prevent-display-sleep');
console.log(`[Kiosk] Sleep blocker active: ${powerSaveBlocker.isStarted(sleepBlockerId)}`);

// ── Create the kiosk window ──
function createKioskWindow() {
  const displays = screen.getAllDisplays();
  const targetDisplay = displays[0]; // use primary display
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
      autoplayPolicy: 'no-user-gesture-required',
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      backgroundThrottling: false,
    },
  });

  // ── Load with retry ──
  loadWithRetry();

  // ── Watchdog: restart if renderer crashes ──
  mainWindow.webContents.on('crashed', () => {
    console.error('[Kiosk] Renderer crashed — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.webContents.on('unresponsive', () => {
    console.warn('[Kiosk] Renderer unresponsive — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.on('closed', () => {
    if (!isQuitting) {
      console.log('[Kiosk] Window closed unexpectedly — recreating...');
      mainWindow = null;
      setTimeout(createKioskWindow, CRASH_RECOVERY_DELAY);
    }
  });

  // ── Inject cursor auto-hide ──
  mainWindow.webContents.on('dom-ready', () => {
    mainWindow.webContents
      .insertCSS(`
        html { cursor: none; }
        * { cursor: none !important; }
      `)
      .catch(() => {});
  });

  // ── Show cursor on window focus, hide after delay ──
  let cursorTimer = null;
  mainWindow.on('focus', () => {
    mainWindow.webContents
      .insertCSS(`html { cursor: default; }`)
      .catch(() => {});
    clearTimeout(cursorTimer);
    cursorTimer = setTimeout(() => {
      mainWindow.webContents
        .insertCSS(`html { cursor: none; } * { cursor: none !important; }`)
        .catch(() => {});
    }, CURSOR_HIDE_DELAY);
  });
}

// ── Load URL with retry ──
function loadWithRetry() {
  if (!mainWindow) return;

  mainWindow.loadURL(DISPLAY_URL).catch((err) => {
    console.warn(`[Kiosk] Load failed: ${err.message}. Retrying in ${RETRY_INTERVAL}ms...`);
    setTimeout(loadWithRetry, RETRY_INTERVAL);
  });
}

// ── Restart: destroy and recreate ──
function restartKiosk() {
  if (mainWindow) {
    mainWindow.destroy();
    mainWindow = null;
  }
  createKioskWindow();
}

// ── Watchdog health check (pings the page every 30s) ──
function startWatchdog() {
  watchdogTimer = setInterval(() => {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    mainWindow.webContents
      .executeJavaScript('true')
      .catch(() => {
        console.warn('[Kiosk] Watchdog: page unresponsive — restarting...');
        restartKiosk();
      });
  }, 30000);
}

// ── Quit handler ──
app.on('before-quit', () => {
  isQuitting = true;
  if (watchdogTimer) {
    clearInterval(watchdogTimer);
    watchdogTimer = null;
  }
  if (powerSaveBlocker.isStarted(sleepBlockerId)) {
    powerSaveBlocker.stop(sleepBlockerId);
  }
});

app.on('window-all-closed', () => {
  // On kiosk mode, stay running and recreate window
  if (!isQuitting) {
    setTimeout(createKioskWindow, 1000);
  }
});

// ── Prevent Alt+F4 from closing the app entirely ──
app.on('will-quit', (event) => {
  if (!isQuitting) {
    event.preventDefault();
  }
});

// ── Start ──
app.whenReady().then(() => {
  createKioskWindow();
  startWatchdog();
  console.log(`[Kiosk] Started — URL: ${DISPLAY_URL}`);
});

app.on('activate', () => {
  if (!mainWindow) createKioskWindow();
});
