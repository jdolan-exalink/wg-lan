export type PeerType = "roadwarrior" | "branch_office" | "server";
export type DeviceType = "laptop" | "ios" | "android" | "router" | "server" | "user";
export type TunnelMode = "full" | "split";
export type SyncStatus = "green" | "yellow" | "red";

export interface Peer {
  id: number;
  name: string;
  peer_type: PeerType;
  device_type: DeviceType | null;
  public_key: string;
  assigned_ip: string;
  network_id: number | null;
  tunnel_mode: TunnelMode;
  remote_subnets: string[];
  dns: string | null;
  persistent_keepalive: number;
  is_enabled: boolean;
  is_system: boolean;
  group_ids: number[];
  created_at: string;
  updated_at: string;
  revoked_at: string | null;
  is_online: boolean;
  sync_status: SyncStatus;
}

export interface PeerStatus {
  id: number;
  name: string;
  peer_type: PeerType;
  assigned_ip: string;
  is_enabled: boolean;
  is_online: boolean;
  endpoint: string | null;
  last_handshake: number;
  rx_bytes: number;
  tx_bytes: number;
}

export interface RoadWarriorCreate {
  name: string;
  device_type: DeviceType;
  tunnel_mode: TunnelMode;
  network_id?: number | null;
  dns?: string;
  group_ids: number[];
  persistent_keepalive: number;
}

export interface BranchOfficeCreate {
  name: string;
  device_type: "router" | "server";
  network_id?: number | null;
  remote_subnets: string[];
  dns?: string;
  group_ids: number[];
  persistent_keepalive: number;
}

export interface PermissionSummary {
  group_policies: Array<{ zone_id: number; zone_name: string; action: string; source: string; group_id: number }>;
  overrides: Array<{ zone_id: number; zone_name: string; action: string; source: string; reason: string | null }>;
  final_cidrs: string[];
}

export interface PeerSyncStatus {
  peer_id: number;
  peer_name: string;
  sync_status: SyncStatus;
  sync_message: string;
  is_online: boolean;
  last_config_downloaded_at: string | null;
  last_config_changed_at: string | null;
}
