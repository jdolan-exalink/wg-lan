import client from "./client";
import type { Network, Zone, PeerGroup, Policy, PolicyMatrix } from "@/types/network";

export const networksApi = {
  list: () => client.get<Network[]>("/networks"),
  create: (data: Omit<Network, "id">) => client.post<Network>("/networks", data),
  update: (id: number, data: Partial<Network>) => client.patch<Network>(`/networks/${id}`, data),
  delete: (id: number) => client.delete(`/networks/${id}`),
  checkConflict: (subnet: string, exclude_id?: number) =>
    client.post<{ has_conflict: boolean; conflicting_network: string | null }>(
      "/networks/check-conflict",
      { subnet, exclude_id }
    ),
};

export const zonesApi = {
  list: () => client.get<Zone[]>("/zones"),
  get: (id: number) => client.get<Zone>(`/zones/${id}`),
  create: (data: { name: string; description?: string; networks: { cidr: string }[] }) =>
    client.post<Zone>("/zones", data),
  update: (id: number, data: { name?: string; description?: string }) =>
    client.patch<Zone>(`/zones/${id}`, data),
  delete: (id: number) => client.delete(`/zones/${id}`),
  addNetwork: (zone_id: number, cidr: string, description?: string) =>
    client.post(`/zones/${zone_id}/networks`, { cidr, description }),
  deleteNetwork: (zone_id: number, zn_id: number) =>
    client.delete(`/zones/${zone_id}/networks/${zn_id}`),
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
};

export const policiesApi = {
  list: (group_id?: number, zone_id?: number) =>
    client.get<Policy[]>("/policies", { params: { group_id, zone_id } }),
  matrix: () => client.get<PolicyMatrix>("/policies/matrix"),
  upsert: (group_id: number, zone_id: number, action: "allow" | "deny") =>
    client.post<Policy>("/policies", { group_id, zone_id, action }),
  delete: (id: number) => client.delete(`/policies/${id}`),
};
