import client from "./client";

export interface ExpectedRoute {
  network_id: number;
  name: string;
  destination: string;
  peer_id: number | null;
  peer_name: string | null;
  gateway: string | null;
  interface: string | null;
  enabled: boolean;
  status: "active" | "missing" | "conflict" | "connected" | "unconfigured" | "disabled";
  message: string;
}
export interface SystemRoute {
  destination: string;
  gateway: string | null;
  interface: string | null;
  table: string;
  protocol: string;
  scope: string | null;
  route_type: string;
  metric: number | null;
  managed: boolean;
}
export interface RouteInventory {
  expected: ExpectedRoute[];
  routes: SystemRoute[];
  warnings: string[];
}
export const routesApi = {
  list: () => client.get<RouteInventory>("/routes"),
  reconcile: () => client.post<RouteInventory>("/routes/reconcile"),
};
