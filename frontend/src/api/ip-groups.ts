import client from "./client";
import type { IpGroup, IpGroupEntry } from "@/types/ip-group";

export const ipGroupsApi = {
  list: (networkId?: number) => {
    const params = networkId ? `?network_id=${networkId}` : "";
    return client.get<IpGroup[]>(`/ip-groups${params}`);
  },

  get: (id: number) => client.get<IpGroup>(`/ip-groups/${id}`),

  create: (data: { name: string; network_id: number; description?: string; entries?: Array<{ ip_address: string; label?: string }> }) =>
    client.post<IpGroup>("/ip-groups", data),

  update: (id: number, data: { name?: string; description?: string }) =>
    client.patch<IpGroup>(`/ip-groups/${id}`, data),

  delete: (id: number) => client.delete(`/ip-groups/${id}`),

  addEntry: (ipGroupId: number, entry: { ip_address: string; label?: string }) =>
    client.post<IpGroupEntry>(`/ip-groups/${ipGroupId}/entries`, entry),

  deleteEntry: (ipGroupId: number, entryId: number) =>
    client.delete(`/ip-groups/${ipGroupId}/entries/${entryId}`),
};
