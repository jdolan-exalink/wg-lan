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
  client_retry_enabled: boolean;
  admin_port: number;
  api_http_port: number;
  api_https_port: number;
  api_http_enabled: boolean;
  vpn_domain: string | null;
}

export interface ServerConfigUpdate {
  address?: string;
  listen_port?: number;
  endpoint?: string;
  dns?: string | null;
  mtu?: number | null;
  post_up?: string | null;
  post_down?: string | null;
  client_retry_enabled?: boolean;
  admin_port?: number;
  api_http_port?: number;
  api_https_port?: number;
  api_http_enabled?: boolean;
  vpn_domain?: string | null;
}

export interface RegenerateKeyResponse {
  public_key: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  db: string;
  wg_interface: string;
  tunnel_count: number;
  uptime_seconds: number;
  is_initialized: boolean;
}

export interface SystemMetrics {
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  cpu_percent: number;
  cpu_count: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
}

export interface ADConfig {
  ad_enabled: boolean;
  ad_server: string | null;
  ad_server_backup: string | null;
  ad_base_dn: string | null;
  ad_bind_dn: string | null;
  ad_user_filter: string | null;
  ad_group_filter: string | null;
  ad_use_ssl: boolean;
  ad_require_membership: boolean;
}

export interface ADConfigUpdate {
  ad_enabled?: boolean;
  ad_server?: string | null;
  ad_server_backup?: string | null;
  ad_base_dn?: string | null;
  ad_bind_dn?: string | null;
  ad_bind_password?: string | null;
  ad_user_filter?: string | null;
  ad_group_filter?: string | null;
  ad_use_ssl?: boolean;
  ad_require_membership?: boolean;
}

export interface ADGroupMapping {
  id: number;
  ad_group_dn: string;
  ad_group_name: string;
  netloom_group_id: number;
  netloom_group_name: string | null;
  enabled: boolean;
  priority: number;
}

export interface ADGroupMappingCreate {
  ad_group_dn: string;
  ad_group_name: string;
  netloom_group_id: number;
  enabled?: boolean;
  priority?: number;
}

export interface ADGroupFromAD {
  dn: string;
  name: string;
  sam_name: string;
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
  getMetrics: () => client.get<SystemMetrics>("/system/metrics"),
  exportBackup: async () => {
    const response = await client.get("/system/backup/export", { responseType: "blob" });
    const contentDisposition = response.headers["content-disposition"] ?? "";
    const match = contentDisposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : "netloom_backup.zip";
    const url = URL.createObjectURL(response.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
  importBackup: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post("/system/backup/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getADConfig: () => client.get<ADConfig>("/system/ad"),
  updateADConfig: (data: ADConfigUpdate) => client.put<ADConfig>("/system/ad", data),
  testADConnection: () => client.post<{ success: boolean; error?: string; message?: string }>("/system/ad/test-connection"),
  getADGroupsFromServer: () => client.get<{ groups: ADGroupFromAD[] }>("/system/ad/groups"),
  getADGroupMappings: () => client.get<ADGroupMapping[]>("/system/ad/group-mappings"),
  createADGroupMapping: (data: ADGroupMappingCreate) => client.post<ADGroupMapping>("/system/ad/group-mappings", data),
  bulkCreateADGroupMappings: (mappings: ADGroupMappingCreate[]) => 
    client.post<ADGroupMapping[]>("/system/ad/group-mappings/bulk", { mappings }),
  updateADGroupMapping: (id: number, data: Partial<ADGroupMapping>) => 
    client.patch<ADGroupMapping>(`/system/ad/group-mappings/${id}`, data),
  deleteADGroupMapping: (id: number) => client.delete(`/system/ad/group-mappings/${id}`),
  resetOnboarding: () => client.post<{ message: string }>("/onboarding/reset"),
};
