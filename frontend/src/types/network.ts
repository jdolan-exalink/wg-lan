export interface Network {
  id: number;
  name: string;
  subnet: string;
  description: string | null;
  network_type: "lan" | "vpn";
  is_default: boolean;
  peer_count: number;
  peers: Array<{
    id: number;
    name: string;
    peer_type: string;
    assigned_ip: string;
    device_type: string | null;
  }>;
}

export interface Zone {
  id: number;
  name: string;
  description: string | null;
  networks: ZoneNetwork[];
}

export interface ZoneNetwork {
  id: number;
  cidr: string;
  description: string | null;
}

export interface PeerGroup {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
}

export interface Policy {
  id: number;
  group_id: number;
  zone_id: number;
  action: "allow" | "deny";
}

export interface PolicyMatrixCell {
  action: "allow" | "deny" | null;
  policy_id: number | null;
}

export interface PolicyMatrixRow {
  group_id: number;
  group_name: string;
  zones: Record<number, PolicyMatrixCell>;
}

export interface PolicyMatrix {
  groups: PolicyMatrixRow[];
  zone_ids: number[];
  zone_names: Record<number, string>;
}
