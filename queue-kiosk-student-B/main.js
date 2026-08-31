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

  // Inject print-only styles matching the working web @media print
  const printCSS = `
    @page { margin: 0 !important; }
    html, body { margin: 0 !important; padding: 0 !important; height: auto !important; overflow: hidden !important; }
    body { background: white !important; display: block !important; }
    .container { max-width: 100% !important; height: auto !important; }
    .card { box-shadow: none !important; border-radius: 0 !important; padding: 6px !important; }
    .header, .step-indicator, .ai-panel, .error-bar, .loading-overlay, .rate-card, .mandatory-notice, .token-actions, .token-notice, .launch-center, .btn-row, .offline-banner, .online-banner { display: none !important; }
    #tokenDisplay, #printArea, .token-result { height: auto !important; max-height: none !important; page-break-inside: avoid !important; padding: 0 !important; }
    .token-badge { background: white !important; border: 1px solid #155c30; border-radius: 10px; padding: 10px 20px 8px !important; box-shadow: none !important; margin-bottom: 6px !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .token-number { font-size: 30px !important; text-shadow: none !important; color: #d4aa00 !important; }
    .token-label { margin-bottom: 2px !important; opacity: 1 !important; color: #155c30 !important; }
    .token-meta { margin-top: 2px !important; font-size: 9px !important; opacity: 1 !important; color: #155c30 !important; }
    .token-details { background: white !important; border: 1px solid #e2e0da; border-radius: 6px; padding: 6px 10px !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .token-row { font-size: 10px !important; padding: 2px 0 !important; }
    .token-row .lbl { color: #6b7280 !important; }
    .token-row .val { color: #155c30 !important; }
    .receipt-header { display: block !important; margin-bottom: 6px !important; padding-bottom: 6px !important; border-bottom-width: 1.5px !important; }
    .receipt-header .rh-brand { font-size: 13px !important; color: #155c30 !important; }
    .receipt-header .rh-brand svg { width: 13px !important; height: 13px !important; fill: #155c30 !important; }
    .receipt-header p { font-size: 9px !important; margin-top: 1px !important; color: #6b7280 !important; }
    .qr-wrap { margin: 4px 0 2px !important; }
    .qr-img { width: 100px !important; height: 100px !important; border-radius: 4px !important; }
    .qr-label { font-size: 8px !important; margin-top: 2px !important; color: #6b7280 !important; }
    .qr-fallback { display: none !important; }
    .receipt-footer { display: block !important; margin-top: 4px !important; padding-top: 4px !important; font-size: 9px !important; color: #6b7280 !important; border-top-width: .5px !important; }
  `;

  await mainWindow.webContents.insertCSS(printCSS);

  mainWindow.webContents.print({
    silent: true,
    printBackground: true,
    headerFooter: false,
    margins: { marginType: 'none' },
    pageSize: { width: 220000, height: 330000 }, // 80mm x 297mm (continuous roll)
    deviceName: deviceName || undefined
  }, (ok, err) => {
    if (!ok) console.warn('[StudentKioskB] Silent print failed:', err);
    // Remove injected CSS after printing
    mainWindow.webContents.insertCSS('');
  });
});

app.on('activate', () => {
  if (!mainWindow) createKioskWindow();
});
