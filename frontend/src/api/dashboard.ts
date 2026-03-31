import client from "./client";
import type { DashboardStats, TrafficItem } from "@/types/dashboard";
import type { PeerStatus } from "@/types/peer";

export const dashboardApi = {
  stats: () => client.get<DashboardStats>("/dashboard/stats"),
  peersStatus: () => client.get<PeerStatus[]>("/dashboard/peers-status"),
  traffic: () => client.get<TrafficItem[]>("/dashboard/traffic"),
};
