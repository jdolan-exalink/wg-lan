import client from "./client";
import type { Peer, RoadWarriorCreate, BranchOfficeCreate, PermissionSummary } from "@/types/peer";

export const peersApi = {
  list: (peer_type?: string) =>
    client.get<Peer[]>("/peers", { params: peer_type ? { peer_type } : {} }),

  get: (id: number) => client.get<Peer>(`/peers/${id}`),

  createRoadWarrior: (data: RoadWarriorCreate) =>
    client.post<Peer>("/peers/roadwarrior", data),

  createBranchOffice: (data: BranchOfficeCreate) =>
    client.post<Peer>("/peers/branch-office", data),

  update: (id: number, data: Partial<Peer>) =>
    client.patch<Peer>(`/peers/${id}`, data),

  updateGroups: (id: number, peer_ids: number[]) =>
    client.post<Peer>(`/peers/${id}/groups`, { peer_ids }),

  revoke: (id: number) => client.delete<{ message: string }>(`/peers/${id}`),

  toggle: (id: number) => client.post<Peer>(`/peers/${id}/toggle`),

  regenerateKeys: (id: number) => client.post<Peer>(`/peers/${id}/regenerate-keys`),

  configUrl: (id: number) => `/api/peers/${id}/config`,

  mikrotikConfigUrl: (id: number) => `/api/peers/${id}/config/mikrotik`,

  qrcodeUrl: (id: number) => `/api/peers/${id}/qrcode`,

  getPermissions: (id: number) =>
    client.get<PermissionSummary>(`/peers/${id}/permissions`),

  upsertOverride: (id: number, zone_id: number, action: "allow" | "deny", reason?: string) =>
    client.post(`/peers/${id}/overrides`, { zone_id, action, reason }),

  deleteOverride: (id: number, zone_id: number) =>
    client.delete(`/peers/${id}/overrides/${zone_id}`),
};
