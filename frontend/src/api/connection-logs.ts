import client from "./client";
import type { ConnectionLog, ConnectionStats } from "@/types/connection-log";

export const connectionLogsApi = {
  list: (params?: { limit?: number; offset?: number; event_type?: string; severity?: string; peer_id?: number }) =>
    client.get<ConnectionLog[]>("/connection-logs", { params }),
  stats: () => client.get<ConnectionStats>("/connection-logs/stats"),
  sync: () => client.post("/connection-logs/sync"),
};
