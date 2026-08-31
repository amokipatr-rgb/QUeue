const { app, BrowserWindow, screen, powerSaveBlocker, ipcMain, session } = require('electron');
const path = require('path');

const DISPLAY_URL = process.env.KIOSK_STUDENT_B_URL
  || 'https://queue-production-2a11.up.railway.app/student-kiosk-B.html';
const RETRY_INTERVAL = 3000;
const CRASH_RECOVERY_DELAY = 2000;
const MAX_RETRIES = 30;

let mainWindow = null;
let watchdogTimer = null;
let isQuitting = false;
let retryCount = 0;

let sleepBlockerId = null;
try {
  sleepBlockerId = powerSaveBlocker.start('prevent-display-sleep');
  console.log(`[StudentKioskB] Sleep blocker active`);
} catch (e) {
  console.warn('[StudentKioskB] Could not start sleep blocker');
}

app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  console.warn(`[StudentKioskB] Certificate error for ${url}: ${error}`);
  event.preventDefault();
  callback(true);
});

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
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      backgroundThrottling: false,
    },
  });

  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!DOCTYPE html>
    <html>
    <head><style>
      *{margin:0;padding:0;box-sizing:border-box}
      body{background:#070d09;color:#fff;font-family:'Segoe UI',sans-serif;
        display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}
      .wrap{text-align:center}
      .shield{width:64px;height:64px;margin:0 auto 20px;
        background:radial-gradient(circle at 40% 35%,#e8c547,#a07c18);
        border-radius:50%;display:flex;align-items:center;justify-content:center}
      .shield svg{width:32px;height:32px;fill:#0f2318}
      h2{font-size:20px;font-weight:400;margin-bottom:8px;opacity:.8}
      .dots{display:inline-flex;gap:4px}
      .dots span{width:8px;height:8px;background:#e8c547;border-radius:50%;
        animation:dotPulse 1.4s ease-in-out infinite}
      .dots span:nth-child(2){animation-delay:.2s}
      .dots span:nth-child(3){animation-delay:.4s}
      @keyframes dotPulse{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}
    </style></head>
    <body>
      <div class="wrap">
        <div class="shield"><svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg></div>
        <h2>Loading Kiosk</h2>
        <div class="dots"><span></span><span></span><span></span></div>
      </div>
    </body>
    </html>
  `)}`);

  loadWithRetry();

  mainWindow.webContents.on('crashed', () => {
    console.error('[StudentKioskB] Renderer crashed — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.webContents.on('unresponsive', () => {
    console.warn('[StudentKioskB] Renderer unresponsive — restarting...');
    setTimeout(restartKiosk, CRASH_RECOVERY_DELAY);
  });

  mainWindow.on('closed', () => {
    if (!isQuitting) {
      console.log('[StudentKioskB] Window closed — recreating...');
      mainWindow = null;
      setTimeout(createKioskWindow, CRASH_RECOVERY_DELAY);
    }
  });
}

function loadWithRetry() {
  if (!mainWindow) return;

  mainWindow.loadURL(DISPLAY_URL).then(() => {
    retryCount = 0;
  }).catch((err) => {
    retryCount++;
    console.warn(`[StudentKioskB] Load failed (${retryCount}): ${err.message}`);
    if (retryCount < MAX_RETRIES) {
      setTimeout(loadWithRetry, RETRY_INTERVAL);
    } else {
      console.error('[StudentKioskB] Max retries — restarting window...');
      setTimeout(restartKiosk, RETRY_INTERVAL);
    }
  });
}

function restartKiosk() {
  retryCount = 0;
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
        console.warn('[StudentKioskB] Watchdog: unresponsive — restarting...');
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
  session.defaultSession.clearCache()
    .then(() => console.log('[StudentKioskB] HTTP cache cleared'))
    .catch((e) => console.warn('[StudentKioskB] Cache clear failed:', e));
  createKioskWindow();
  startWatchdog();
  console.log(`[StudentKioskB] Started — URL: ${DISPLAY_URL}`);
});

// ── Silent receipt printing ──
async function findReceiptPrinter(contents) {
  try {
    const printers = await contents.getPrintersAsync();
    const match = printers.find(p =>
      /POSPrinter|80C/i.test(p.name) || /POSPrinter|80C/i.test(p.displayName)
    );
    if (match) {
      console.log(`[StudentKioskB] Receipt printer detected: ${match.name} (${match.displayName})`);
      return match.name;
    }
    console.warn(`[StudentKioskB] No POSPrinter found. Available: ${printers.map(p => p.name).join(' | ')}`);
  } catch (e) {
    console.warn('[StudentKioskB] Printer detection failed:', e);
  }
  return process.env.RECEIPT_PRINTER || '';
}

ipcMain.on('print-receipt', async (event) => {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const deviceName = await findReceiptPrinter(mainWindow.webContents);

  // No CSS injection — let the page's own @media print handle styling
  // (the HTML file already has working print CSS)
  mainWindow.webContents.print({
    silent: true,
    printBackground: true,
    headerFooter: false,
    margins: { marginType: 'none' },
    deviceName: deviceName || undefined
  }, (ok, err) => {
    if (!ok) console.warn('[StudentKioskB] Silent print failed:', err);
  });
});

app.on('activate', () => {
  if (!mainWindow) createKioskWindow();
});
