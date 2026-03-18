const { app, BrowserWindow } = require("electron");
const { spawn } = require("node:child_process");
const http = require("node:http");
const path = require("node:path");
const fs = require("node:fs");

let backendProcess = null;
let staticServer = null;

function getRuntimeDataDir() {
  if (app.isPackaged) {
    return path.join(path.dirname(process.execPath), "data");
  }
  return path.join(__dirname, "..", "..", "..", ".examnova-data");
}

const runtimeDataDir = getRuntimeDataDir();
fs.mkdirSync(runtimeDataDir, { recursive: true });
app.setPath("userData", path.join(runtimeDataDir, "electron"));
app.setPath("sessionData", path.join(runtimeDataDir, "electron-cache"));
app.setPath("logs", path.join(runtimeDataDir, "logs"));

function getBackendCommand() {
  if (app.isPackaged) {
    const exePath = path.join(process.resourcesPath, "backend", "examnova-backend.exe");
    return { command: exePath, args: [] };
  }

  return {
    command: "python",
    args: ["run_backend.py"],
    cwd: path.join(__dirname, "..", "..", "backend"),
  };
}

function startBackend() {
  const backend = getBackendCommand();
  if (app.isPackaged && !fs.existsSync(backend.command)) {
    return;
  }

  backendProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    env: {
      ...process.env,
      EXAMNOVA_BACKEND_HOST: "127.0.0.1",
      EXAMNOVA_BACKEND_PORT: "8000",
      EXAMNOVA_DATA_DIR: path.join(runtimeDataDir, "backend"),
    },
    stdio: "ignore",
    windowsHide: true,
  });
}

function resolveContentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const table = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
  };
  return table[ext] || "application/octet-stream";
}

function createStaticServer() {
  const webRoot = path.join(__dirname, "..", "out");
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
      const relativePath = urlPath === "/" ? "index.html" : urlPath.replace(/^\/+/, "");
      let filePath = path.join(webRoot, relativePath);

      if (!filePath.startsWith(webRoot)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }

      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(webRoot, "index.html");
      }

      fs.readFile(filePath, (error, data) => {
        if (error) {
          res.writeHead(500);
          res.end("Failed to read file");
          return;
        }
        res.writeHead(200, { "Content-Type": resolveContentType(filePath) });
        res.end(data);
      });
    });

    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        reject(new Error("Unable to start static server"));
        return;
      }
      staticServer = server;
      resolve(`http://127.0.0.1:${address.port}`);
    });
  });
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1600,
    height: 980,
    minWidth: 1280,
    minHeight: 800,
    backgroundColor: "#f8f7f4",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (process.env.EXAMNOVA_DESKTOP_URL) {
    win.loadURL(process.env.EXAMNOVA_DESKTOP_URL);
    return;
  }

  const localUrl = await createStaticServer();
  win.loadURL(localUrl);
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  if (staticServer) {
    staticServer.close();
  }
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});
