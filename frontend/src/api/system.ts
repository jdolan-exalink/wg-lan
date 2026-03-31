import client from "./client";

export interface ServerConfig {
  id: number;
  interface_name: string;
  public_key: string;
  listen_port: number;
  address: string;
  dns: string | null;
  mtu: number | null;
  post_up: string | null;
  post_down: string | null;
  endpoint: string;
}

export interface ServerConfigUpdate {
  address?: string;
  listen_port?: number;
  endpoint?: string;
  dns?: string | null;
  mtu?: number | null;
  post_up?: string | null;
  post_down?: string | null;
}

export interface RegenerateKeyResponse {
  public_key: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  db: string;
  wg_interface: string;
}

export const systemApi = {
  health: () => client.get<HealthResponse>("/system/health"),
  getServerConfig: () => client.get<ServerConfig>("/system/server-config"),
  updateServerConfig: (data: ServerConfigUpdate) =>
    client.put<ServerConfig>("/system/server-config", data),
  regenerateKey: () => client.post<RegenerateKeyResponse>("/system/server-config/regenerate-key"),
  applyConfig: () => client.post<{ message: string }>("/system/apply-config"),
  wgUp: () => client.post<{ message: string }>("/system/wg/up"),
  wgDown: () => client.post<{ message: string }>("/system/wg/down"),
  wgRestart: () => client.post<{ message: string }>("/system/wg/restart"),
  backup: () => client.post<{ message: string; path: string }>("/system/backup"),
};
