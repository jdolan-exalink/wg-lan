export interface Network {
  id: number;
  name: string;
  subnet: string;
  description: string | null;
  network_type: "lan" | "vpn";
  is_default: boolean;
  peer_id: number | null;
  peer_count: number;
  peers: Array<{
    id: number;
    name: string;
    peer_type: string;
    assigned_ip: string;
    device_type: string | null;
  }>;
}

export interface PeerGroup {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
}

export interface Policy {
  id: number;
  source_group_id: number;
  source_group_name: string | null;
  dest_group_id: number | null;
  dest_group_name: string | null;
  dest_ip_group_id: number | null;
  dest_ip_group_name: string | null;
  direction: "outbound" | "inbound" | "both";
  action: "allow" | "deny";
  enabled: boolean;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface FirewallStatus {
  firewall_enabled: boolean;
}

export interface PolicyMatrixCell {
  action: "allow" | "deny" | null;
  policy_id: number | null;
  direction: "outbound" | "inbound" | "both" | null;
}

export interface PolicyMatrixRow {
  source_group_id: number;
  source_group_name: string;
  dest_groups: Record<number, PolicyMatrixCell>;
}

export interface PolicyMatrix {
  source_groups: PolicyMatrixRow[];
  dest_group_ids: number[];
  dest_group_names: Record<number, string>;
}
