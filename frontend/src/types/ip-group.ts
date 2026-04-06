export interface IpGroupEntry {
  id: number;
  ip_group_id: number;
  ip_address: string;
  label: string | null;
  created_at: string;
}

export interface IpGroup {
  id: number;
  name: string;
  network_id: number;
  network_name: string | null;
  subnet: string | null;
  description: string | null;
  entry_count: number;
  entries: IpGroupEntry[];
  created_at: string;
  updated_at: string;
}
