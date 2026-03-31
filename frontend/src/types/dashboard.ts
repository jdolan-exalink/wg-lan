export interface DashboardStats {
  total_peers: number;
  online_peers: number;
  offline_peers: number;
  total_rx_bytes: number;
  total_tx_bytes: number;
  roadwarrior_count: number;
  branch_office_count: number;
}

export interface TrafficItem {
  peer_id: number;
  peer_name: string;
  rx_bytes: number;
  tx_bytes: number;
}
