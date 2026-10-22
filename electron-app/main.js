const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

const LOCAL_API_URL = 'http://localhost:8000';
const RENDER_API_URL = 'https://kiri-tts-api.onrender.com';

function checkLocalServer() {
  return new Promise((resolve) => {
    const req = http.get(`${LOCAL_API_URL}/health`, { timeout: 1500 }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

function startPythonBackend() {
  const rootDir = path.join(__dirname, '..');
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  
  console.log('Starting Python backend process...');
  pythonProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'api:app', '--host', '0.0.0.0', '--port', '8000'], {
    cwd: rootDir,
    stdio: 'ignore',
    detached: false
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python backend:', err);
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 780,
    minWidth: 920,
    minHeight: 640,
    backgroundColor: '#0B0F19',
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Check backend server on startup
  const isLocalAlive = await checkLocalServer();
  if (!isLocalAlive) {
    console.log('Local server not detected, launching background backend...');
    startPythonBackend();
  }
}

// IPC Handlers
ipcMain.handle('get-server-status', async () => {
  const localOk = await checkLocalServer();
  return {
    localAvailable: localOk,
    localUrl: LOCAL_API_URL,
    renderUrl: RENDER_API_URL
  };
});

ipcMain.handle('save-audio-file', async (event, { filename, arrayBuffer }) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    title: 'រក្សាទុកឯកសារសំឡេង (Save MP3)',
    defaultPath: filename || 'kiri_khmer_speech.mp3',
    filters: [
      { name: 'MP3 Audio (*.mp3)', extensions: ['mp3'] },
      { name: 'All Files (*.*)', extensions: ['*'] }
    ]
  });

  if (canceled || !filePath) {
    return { success: false, message: 'Canceled by user' };
  }

  try {
    const buffer = Buffer.from(arrayBuffer);
    fs.writeFileSync(filePath, buffer);
    return { success: true, filePath };
  } catch (err) {
    return { success: false, message: err.message };
  }
});

ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
});

ipcMain.on('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) mainWindow.unmaximize();
    else mainWindow.maximize();
  }
});

ipcMain.on('window-close', () => {
  if (mainWindow) mainWindow.close();
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch {}
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
