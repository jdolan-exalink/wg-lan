import client from "./client";
import type { FirewallStatus, Network, PeerGroup, Policy, PolicyMatrix } from "@/types/network";
import type { Peer } from "@/types/peer";

export const networksApi = {
  list: () => client.get<Network[]>("/networks"),
  create: (data: Omit<Network, "id">) => client.post<Network>("/networks", data),
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
};

export const policiesApi = {
  list: (source_group_id?: number, dest_group_id?: number) =>
    client.get<Policy[]>("/policies", { params: { source_group_id, dest_group_id } }),
  matrix: () => client.get<PolicyMatrix>("/policies/matrix"),
  create: (data: { source_group_id: number; dest_group_id: number; direction: "outbound" | "inbound" | "both"; action: "allow" | "deny"; enabled?: boolean }) =>
    client.post<Policy>("/policies", data),
  update: (id: number, data: { direction?: "outbound" | "inbound" | "both"; action?: "allow" | "deny"; enabled?: boolean }) =>
    client.patch<Policy>(`/policies/${id}`, data),
  delete: (id: number) => client.delete(`/policies/${id}`),
};

export const firewallApi = {
  getStatus: () => client.get<FirewallStatus>("/system/firewall"),
  setStatus: (firewall_enabled: boolean) =>
    client.patch<FirewallStatus>("/system/firewall", { firewall_enabled }),
};
