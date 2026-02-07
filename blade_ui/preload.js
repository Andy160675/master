// Preload exposing IPC bridge
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('BladeAPI', {
  evalAgency: (features) => ipcRenderer.invoke('agency:eval', features),
  queryTruth: (question) => ipcRenderer.invoke('truth:query', question),
  getSovereignStatus: () => ipcRenderer.invoke('sovereign:status'),
  getConnectionConfig: () => ipcRenderer.invoke('config:get')
});
