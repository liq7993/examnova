const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("examnovaDesktop", {
  platform: process.platform,
});
