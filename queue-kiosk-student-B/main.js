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

  // Inject print-only styles to isolate receipt content for 80mm POS printer
  const printCSS = `
    @page { size: 80mm auto; margin: 0 !important; }
    * { visibility: hidden !important; }
    #printArea, #printArea * { visibility: visible !important; }
    body { background: white !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
    #printArea {
      position: absolute !important; left: 0 !important; top: 0 !important;
      width: 80mm !important; padding: 4mm !important; margin: 0 !important;
      background: white !important; box-shadow: none !important; border: none !important;
      font-size: 11pt !important; color: #000 !important;
    }
    #printArea .receipt-header { border-bottom: 1px dashed #000 !important; padding-bottom: 4mm !important; margin-bottom: 4mm !important; }
    #printArea .receipt-header .rh-brand { font-size: 14pt !important; font-weight: 700 !important; color: #000 !important; }
    #printArea .receipt-header .rh-brand svg { display: none !important; }
    #printArea .receipt-header p { font-size: 8pt !important; color: #555 !important; }
    #printArea .token-badge { border: 2px solid #000 !important; border-radius: 6px !important; padding: 4mm !important; margin-bottom: 4mm !important; text-align: center !important; background: white !important; }
    #printArea .token-number { font-size: 28pt !important; font-weight: 900 !important; color: #000 !important; text-shadow: none !important; letter-spacing: 2px !important; }
    #printArea .token-label { font-size: 9pt !important; color: #000 !important; margin-bottom: 2mm !important; }
    #printArea .token-meta { font-size: 8pt !important; color: #555 !important; }
    #printArea .token-details { border: 1px solid #ccc !important; border-radius: 4px !important; padding: 3mm !important; margin-bottom: 4mm !important; background: white !important; }
    #printArea .token-row { font-size: 9pt !important; padding: 1mm 0 !important; display: flex !important; justify-content: space-between !important; }
    #printArea .token-row .lbl { color: #555 !important; }
    #printArea .token-row .val { color: #000 !important; font-weight: 600 !important; }
    #printArea .qr-wrap { text-align: center !important; margin: 4mm 0 !important; }
    #printArea .qr-img { width: 35mm !important; height: 35mm !important; border: 1px solid #ccc !important; }
    #printArea .qr-label { font-size: 7pt !important; color: #555 !important; margin-top: 2mm !important; }
    #printArea .qr-fallback { display: none !important; }
    #printArea .mandatory-notice { display: none !important; }
    #printArea .token-notice { font-size: 8pt !important; color: #555 !important; text-align: center !important; font-style: italic !important; margin: 3mm 0 !important; }
    #printArea .token-actions { display: none !important; }
    #printArea .receipt-footer { border-top: 1px dashed #000 !important; padding-top: 3mm !important; margin-top: 3mm !important; text-align: center !important; font-size: 7pt !important; color: #555 !important; }
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
