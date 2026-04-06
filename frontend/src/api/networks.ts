import client from "./client";
import type { FirewallStatus, Network, PeerGroup, Policy, PolicyMatrix } from "@/types/network";
import type { Peer } from "@/types/peer";

export const networksApi = {
  list: () => client.get<Network[]>("/networks"),
  create: (data: { name: string; subnet: string; description?: string; network_type?: string; is_default?: boolean; peer_id?: number | null }) =>
    client.post<Network>("/networks", data),
  update: (id: number, data: Partial<Network>) => client.patch<Network>(`/networks/${id}`, data),
  delete: (id: number) => client.delete(`/networks/${id}`),
  apply: () => client.post("/networks/apply"),
  checkConflict: (subnet: string, exclude_id?: number) =>
    client.post<{ has_conflict: boolean; conflicting_network: string | null }>(
      "/networks/check-conflict",
      { subnet, exclude_id }
    ),
  assignPeers: (networkId: number, peerIds: number[]) =>
    client.post<Network>(`/networks/${networkId}/peers`, { peer_ids: peerIds }),
  addPeer: (networkId: number, peerId: number) =>
    client.post<Network>(`/networks/${networkId}/peers/${peerId}`),
  removePeer: (networkId: number, peerId: number) =>
    client.delete<Network>(`/networks/${networkId}/peers/${peerId}`),
};

export const peersApi = {
  list: () => client.get<Peer[]>("/peers"),
};

export const groupsApi = {
  list: () => client.get<PeerGroup[]>("/groups"),
  get: (id: number) => client.get<PeerGroup>(`/groups/${id}`),
  create: (data: { name: string; description?: string }) =>
    client.post<PeerGroup>("/groups", data),
  update: (id: number, data: { name?: string; description?: string }) =>
    client.patch<PeerGroup>(`/groups/${id}`, data),
  delete: (id: number) => client.delete(`/groups/${id}`),
  addMembers: (group_id: number, peer_ids: number[]) =>
    client.post(`/groups/${group_id}/members`, { peer_ids }),
  removeMember: (group_id: number, peer_id: number) =>
    client.delete(`/groups/${group_id}/members/${peer_id}`),
  getMembers: (group_id: number) =>
    client.get<Array<{ peer_id: number; peer_name: string; peer_type: string; assigned_ip: string }>>(`/groups/${group_id}/members`),
  // Group network access
  getNetworks: (group_id: number) =>
    client.get<Array<{ id: number; network_id: number; network_name: string; subnet: string; network_type: string; action: string }>>(`/groups/${group_id}/networks`),
  assignNetwork: (group_id: number, data: { network_id: number; action: string }) =>
    client.post(`/groups/${group_id}/networks`, data),
  removeNetwork: (group_id: number, network_id: number) =>
    client.delete(`/groups/${group_id}/networks/${network_id}`),
};

export const policiesApi = {
  list: (source_group_id?: number, dest_group_id?: number) =>
    client.get<Policy[]>("/policies", { params: { source_group_id, dest_group_id } }),
  matrix: () => client.get<PolicyMatrix>("/policies/matrix"),
  create: (data: { source_group_id: number; dest_group_id?: number | null; dest_ip_group_id?: number | null; direction: "outbound" | "inbound" | "both"; action: "allow" | "deny"; enabled?: boolean }) =>
    client.post<Policy>("/policies", data),
  update: (id: number, data: { direction?: "outbound" | "inbound" | "both"; action?: "allow" | "deny"; enabled?: boolean }) =>
    client.patch<Policy>(`/policies/${id}`, data),
  delete: (id: number) => client.delete(`/policies/${id}`),
  reorder: (ids: number[]) => client.patch("/policies/reorder", ids),
  firewallRules: () => client.get<Array<{ target: string; src: string; dst: string; extra: string }>>("/policies/firewall-rules"),
};

export const firewallApi = {
  getStatus: () => client.get<FirewallStatus>("/system/firewall"),
  setStatus: (firewall_enabled: boolean) =>
    client.patch<FirewallStatus>("/system/firewall", { firewall_enabled }),
};
