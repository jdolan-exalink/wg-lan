from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_peers: int
    online_peers: int
    offline_peers: int
    total_rx_bytes: int
    total_tx_bytes: int
    roadwarrior_count: int
    branch_office_count: int


class PeerStatusItem(BaseModel):
    id: int
    name: str
    peer_type: str
    assigned_ip: str
    is_enabled: bool
    is_online: bool
    endpoint: str | None
    last_handshake: int  # epoch seconds, 0 = never
    rx_bytes: int
    tx_bytes: int


class TrafficItem(BaseModel):
    peer_id: int
    peer_name: str
    rx_bytes: int
    tx_bytes: int
