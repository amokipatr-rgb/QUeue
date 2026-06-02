const { app, BrowserWindow, shell } = require('electron');
const path = require('path');

const DISPLAY_URL = process.env.KIOSK_INDEX_URL
  || 'https://queue-production-2a11.up.railway.app/';
const CRASH_RECOVERY_DELAY = 2000;
const MAX_RETRIES = 30;

let mainWindow = null;
let isQuitting = false;
let retryCount = 0;

app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  console.warn(`[App] Certificate error for ${url}: ${error}`);
  event.preventDefault();
  callback(true);
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 680,
    center: true,
    title: 'Makerere University — Queue Management System',
    autoHideMenuBar: true,
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

  // Attach event handlers BEFORE loading
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    if (!isQuitting) {
      mainWindow = null;
      setTimeout(createWindow, CRASH_RECOVERY_DELAY);
    }
  });

  mainWindow.webContents.on('crashed', () => {
    console.error('[App] Renderer crashed — restarting...');
    setTimeout(createWindow, CRASH_RECOVERY_DELAY);
  });

  // Show loading screen first
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
        <h2>Loading</h2>
        <div class="dots"><span></span><span></span><span></span></div>
      </div>
    </body>
    </html>
  `)}`);

  loadWithRetry();
}

function loadWithRetry() {
  if (!mainWindow) return;

  mainWindow.loadURL(DISPLAY_URL).then(() => {
    retryCount = 0;
  }).catch((err) => {
    retryCount++;
    console.warn(`[App] Load failed (${retryCount}): ${err.message}`);
    if (retryCount < MAX_RETRIES) {
      setTimeout(loadWithRetry, 2000);
    } else {
      console.error('[App] Max retries — reloading...');
      retryCount = 0;
      setTimeout(loadWithRetry, CRASH_RECOVERY_DELAY);
    }
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' && !isQuitting) app.quit();
});

app.whenReady().then(() => {
  createWindow();
  console.log(`[App] Started — ${DISPLAY_URL}`);
});

app.on('activate', () => {
  if (!mainWindow) createWindow();
});
