import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

export interface User {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  is_admin: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
  last_failed_login_at: string | null;
  failed_login_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserDetail extends User {
  groups: GroupSummary[];
}

export interface GroupSummary {
  id: number;
  name: string;
  description: string | null;
}

export interface Group {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  member_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: number;
  user_id: number;
  device_name: string;
  hostname: string | null;
  os_type: string | null;
  device_fingerprint: string | null;
  status: string;
  last_seen_at: string | null;
  last_sync_at: string | null;
  config_revision: number;
  created_at: string;
  updated_at: string;
}

export interface UserNetworkAssignment {
  id: number;
  network_id: number;
  network_name: string;
  subnet: string;
  network_type: string;
  action: string;
}

export const usersApi = {
  list: (params?: { search?: string; is_active?: boolean; is_admin?: boolean }) =>
    api.get<User[]>("/v1/users", { params }),
  
  get: (id: number) =>
    api.get<UserDetail>(`/v1/users/${id}`),
  
  create: (data: {
    username: string;
    email?: string;
    password: string;
    password_confirm: string;
    is_active?: boolean;
    is_admin?: boolean;
  }) =>
    api.post<User>("/v1/users", data),
  
  update: (id: number, data: {
    email?: string;
    is_active?: boolean;
    is_admin?: boolean;
  }) =>
    api.patch<User>(`/v1/users/${id}`, data),
  
  disable: (id: number) =>
    api.post<User>(`/v1/users/${id}/disable`),
  
  enable: (id: number) =>
    api.post<User>(`/v1/users/${id}/enable`),
  
  resetPassword: (id: number, newPassword: string) =>
    api.post<User>(`/v1/users/${id}/reset-password`, { new_password: newPassword }),
  
  changePassword: (id: number, data: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }) =>
    api.post<{ message: string }>(`/v1/users/${id}/change-password`, data),
  
  getGroups: (id: number) =>
    api.get<GroupSummary[]>(`/v1/users/${id}/groups`),
  
  assignGroups: (id: number, groupIds: number[]) =>
    api.post<GroupSummary[]>(`/v1/users/${id}/groups`, { group_ids: groupIds }),
  
  removeGroup: (userId: number, groupId: number) =>
    api.delete(`/v1/users/${userId}/groups/${groupId}`),

  // User network access
  getNetworks: (id: number) =>
    api.get<UserNetworkAssignment[]>(`/v1/users/${id}/networks`),

  assignNetwork: (id: number, data: { network_id: number; action: string }) =>
    api.post<UserNetworkAssignment>(`/v1/users/${id}/networks`, data),

  removeNetwork: (userId: number, networkId: number) =>
    api.delete(`/v1/users/${userId}/networks/${networkId}`),
};

export const groupsApi = {
  list: () =>
    api.get<Group[]>("/groups"),
  
  get: (id: number) =>
    api.get<Group>(`/groups/${id}`),
  
  create: (data: { name: string; description?: string }) =>
    api.post<Group>("/groups", data),
  
  update: (id: number, data: { name?: string; description?: string; is_active?: boolean }) =>
    api.patch<Group>(`/groups/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/groups/${id}`),
};

export const devicesApi = {
  list: (params?: { user_id?: number; status?: string }) =>
    api.get<Device[]>("/v1/devices", { params }),
  
  get: (id: number) =>
    api.get<Device>(`/v1/devices/${id}`),
  
  update: (id: number, data: { device_name?: string; status?: string }) =>
    api.patch<Device>(`/v1/devices/${id}`, data),
};
