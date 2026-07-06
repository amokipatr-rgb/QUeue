const { app, BrowserWindow, screen, powerSaveBlocker, globalShortcut, session } = require('electron');
const path = require('path');

// ── Configuration ──
const DISPLAY_URL = process.env.KIOSK_URL
  || 'https://queue-production-2a11.up.railway.app/public-display.html'
  // || 'http://localhost:5000/public-display.html';
const RETRY_INTERVAL = 3000;
const CRASH_RECOVERY_DELAY = 2000;
const CURSOR_HIDE_DELAY = 3000;
const MAX_RETRIES = 30;

let mainWindow = null;
let watchdogTimer = null;
let isQuitting = false;
let retryCount = 0;

// ── Prevent system sleep ──
const sleepBlockerId = powerSaveBlocker.start('prevent-display-sleep');
console.log(`[Kiosk] Sleep blocker active: ${powerSaveBlocker.isStarted(sleepBlockerId)}`);

// ── Accept all certificates (Railway SSL) ──
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  console.warn(`[Kiosk] Certificate error for ${url}: ${error}. Proceeding anyway.`);
  event.preventDefault();
  callback(true);
});

// ── Create the kiosk window ──
function createKioskWindow() {
  const displays = screen.getAllDisplays();
  const targetDisplay = displays[0];
  const { x, y, width, height } = targetDisplay.bounds;

  mainWindow = new BrowserWindow({
    x, y, width, height,
    fullscreen: true,
    frame: false,
    resizable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    backgroundColor: '#070d09',
    show: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      autoplayPolicy: 'no-user-gesture-required',
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      backgroundThrottling: false,
    },
  });

  // Show loading HTML immediately to avoid white flash
  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!DOCTYPE html>
    <html>
    <head><style>
      *{margin:0;padding:0;box-sizing:border-box}
      body{
        background:#070d09;color:#fff;
        font-family:'Segoe UI',sans-serif;
        display:flex;align-items:center;justify-content:center;
        height:100vh;overflow:hidden;
      }
      .wrap{text-align:center}
      .shield{width:64px;height:64px;margin:0 auto 20px;
        background:radial-gradient(circle at 40% 35%,#e8c547,#a07c18);
        border-radius:50%;display:flex;align-items:center;justify-content:center;
      }
      .shield svg{width:32px;height:32px;fill:#0f2318}
      h2{font-size:20px;font-weight:400;margin-bottom:8px;opacity:.8}
      .dots{display:inline-flex;gap:4px}
      .dots span{
        width:8px;height:8px;background:#e8c547;border-radius:50%;
        animation:dotPulse 1.4s ease-in-out infinite;
      }
      .dots span:nth-child(2){animation-delay:.2s}
      .dots span:nth-child(3){animation-delay:.4s}
      @keyframes dotPulse{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}
    </style></head>
    <body>
      <div class="wrap">
        <div class="shield">
          <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
        </div>
        <h2>Connecting to server</h2>
        <div class="dots"><span></span><span></span><span></span></div>
      </div>
    </body>
    </html>
  `)}`);

  // ── Load actual URL ──
  loadWithRetry();

  // ── Crash recovery ──
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

  // ── Inject cursor auto-hide after page loads ──
  mainWindow.webContents.on('dom-ready', () => {
    mainWindow.webContents
      .insertCSS(`html { cursor: none; } * { cursor: none !important; }`)
      .catch(() => {});
  });

  // ── Show cursor on focus, hide after delay ──
  let cursorTimer = null;
  mainWindow.on('focus', () => {
    mainWindow.webContents.insertCSS(`html { cursor: default; }`).catch(() => {});
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

  mainWindow.loadURL(DISPLAY_URL).then(() => {
    retryCount = 0;
  }).catch((err) => {
    retryCount++;
    console.warn(`[Kiosk] Load failed (attempt ${retryCount}): ${err.message}`);
    if (retryCount < MAX_RETRIES) {
      setTimeout(loadWithRetry, RETRY_INTERVAL);
    } else {
      console.error('[Kiosk] Max retries reached. Restarting window...');
      setTimeout(restartKiosk, RETRY_INTERVAL);
    }
  });
}

// ── Restart ──
function restartKiosk() {
  retryCount = 0;
  if (mainWindow) {
    mainWindow.destroy();
    mainWindow = null;
  }
  createKioskWindow();
}

// ── Watchdog health check ──
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
  if (!isQuitting) {
    setTimeout(createKioskWindow, 1000);
  }
});

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
