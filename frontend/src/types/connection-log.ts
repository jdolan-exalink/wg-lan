export interface ConnectionLog {
  id: number;
  timestamp: string;
  peer_id: number | null;
  peer_name: string | null;
  peer_ip: string | null;
  event_type: string;
  severity: "info" | "warning" | "error" | "critical";
  message: string;
  details: string | null;
  source_ip: string | null;
  duration_ms: number | null;
}

export interface ConnectionStats {
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_severity: Record<string, number>;
  online_peers: number;
  offline_peers: number;
  peers_with_errors: Array<{
    peer_id: number;
    peer_name: string;
    error_count: number;
    last_error: string;
    last_message: string;
  }>;
}
