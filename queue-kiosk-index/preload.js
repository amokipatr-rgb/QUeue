const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('kiosk', {
  isElectron: true,
});

document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = `
    .hero-actions { display: none !important; }
    .ribbon-nav a:nth-child(1) { display: none !important; }
    .ribbon-nav a:nth-child(3) { display: none !important; }
    .ribbon-nav a:nth-child(4) { display: none !important; }
    .ribbon-nav a:nth-child(5) { display: none !important; }
    .stats-row { display: none !important; }
    .header-clock { display: none !important; }
  `;
  document.head.appendChild(style);
});
