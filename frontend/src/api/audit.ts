import client from "./client";

export interface AuditLog {
  id: number;
  timestamp: string;
  user_id: number | null;
  action: string;
  target_type: string | null;
  target_id: number | null;
  details: string | null;
  ip_address: string | null;
}

export const auditApi = {
  list: (params?: { limit?: number; offset?: number; target_type?: string }) =>
    client.get<AuditLog[]>("/audit", { params }),
};
