// Electron main process skeleton for Blade Boardroom Shell
// Phase 3 - minimal IPC endpoints; expand later
import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function normalizeBaseUrl(url) {
  const s = String(url || '').trim();
  return s.replace(/\/+$/, '');
}

function getConnectionConfig() {
  const truthEngineUrl = normalizeBaseUrl(process.env.TRUTH_ENGINE_URL || 'http://localhost:8000');
  const ollamaHost = normalizeBaseUrl(process.env.OLLAMA_HOST || 'http://localhost:11434');
  const ollamaBaseUrl = normalizeBaseUrl(process.env.OLLAMA_BASE_URL || `${ollamaHost}/v1`);
  return { truthEngineUrl, ollamaHost, ollamaBaseUrl };
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// IPC stubs � will call python backends later
ipcMain.handle('agency:eval', async (_evt, payload) => {
  // placeholder returns static vector; integrate HTTP fetch to python
  return { A1:0.62,A2:0.58,A3:0.51,A4:0.55, AgencyScore:0.57, state:'STEADY' };
});

ipcMain.handle('truth:query', async (_evt, question) => {
  const cfg = getConnectionConfig();
  const endpoint = `${cfg.truthEngineUrl}/truth/query`;
  const payload = { question: String(question || ''), k: 5 };
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      return { answer: `Truth engine error (${res.status})`, cites: [], error: text || res.statusText, endpoint };
    }
    const data = await res.json();
    return { ...data, endpoint };
  } catch (e) {
    return { answer: 'Truth engine unreachable.', cites: [], error: String(e?.message || e), endpoint };
  }
});

ipcMain.handle('config:get', async () => {
  return getConnectionConfig();
});

ipcMain.handle('sovereign:status', async () => {
  return { manifestDate: '2025-11-19', robocopyLast:'04:00 OK', freeSpaceGB: 812, indexStatus:'STALE' };
});
