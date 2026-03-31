import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatBytes, formatHandshake } from "@/lib/utils";
import { Users, Wifi, WifiOff, ArrowDownUp, Router, Laptop } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const POLL_INTERVAL = 10_000;

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardApi.stats().then((r) => r.data),
    refetchInterval: POLL_INTERVAL,
  });

  const { data: peerStatuses = [] } = useQuery({
    queryKey: ["dashboard-peers"],
    queryFn: () => dashboardApi.peersStatus().then((r) => r.data),
    refetchInterval: POLL_INTERVAL,
  });

  const { data: traffic = [] } = useQuery({
    queryKey: ["dashboard-traffic"],
    queryFn: () => dashboardApi.traffic().then((r) => r.data),
    refetchInterval: POLL_INTERVAL,
  });

  const topTraffic = traffic.slice(0, 8).map((t) => ({
    name: t.peer_name.length > 12 ? t.peer_name.slice(0, 12) + "…" : t.peer_name,
    RX: Math.round(t.rx_bytes / 1024),
    TX: Math.round(t.tx_bytes / 1024),
  }));

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={<Users className="h-4 w-4" />} label="Total Peers" value={stats?.total_peers ?? "—"} />
        <StatCard icon={<Wifi className="h-4 w-4 text-green-600" />} label="Online" value={stats?.online_peers ?? "—"} valueClass="text-green-600" />
        <StatCard icon={<WifiOff className="h-4 w-4 text-muted-foreground" />} label="Offline" value={stats?.offline_peers ?? "—"} />
        <StatCard icon={<ArrowDownUp className="h-4 w-4 text-primary" />} label="Total Transfer" value={stats ? formatBytes(stats.total_rx_bytes + stats.total_tx_bytes) : "—"} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Peer Types */}
        <div className="grid grid-cols-2 gap-4">
          <StatCard icon={<Laptop className="h-4 w-4" />} label="RoadWarriors" value={stats?.roadwarrior_count ?? "—"} />
          <StatCard icon={<Router className="h-4 w-4" />} label="Branch Offices" value={stats?.branch_office_count ?? "—"} />
        </div>

        {/* Traffic Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Top Peers by Traffic (KB)</CardTitle>
          </CardHeader>
          <CardContent>
            {topTraffic.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No traffic data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={topTraffic} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => `${v} KB`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="RX" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="TX" fill="#10b981" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Peer Status Table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Peer Status</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Name</th>
                  <th className="text-left px-4 py-2 font-medium">Type</th>
                  <th className="text-left px-4 py-2 font-medium">IP</th>
                  <th className="text-left px-4 py-2 font-medium">Status</th>
                  <th className="text-left px-4 py-2 font-medium">Handshake</th>
                  <th className="text-left px-4 py-2 font-medium">RX / TX</th>
                </tr>
              </thead>
              <tbody>
                {peerStatuses.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      No peers yet
                    </td>
                  </tr>
                ) : (
                  peerStatuses.map((p) => (
                    <tr key={p.id} className="border-b last:border-0 hover:bg-muted/20">
                      <td className="px-4 py-2 font-medium">{p.name}</td>
                      <td className="px-4 py-2 capitalize text-muted-foreground">{p.peer_type.replace("_", " ")}</td>
                      <td className="px-4 py-2 font-mono text-xs">{p.assigned_ip}</td>
                      <td className="px-4 py-2">
                        {!p.is_enabled ? (
                          <Badge variant="outline">Disabled</Badge>
                        ) : p.is_online ? (
                          <Badge variant="success">Online</Badge>
                        ) : (
                          <Badge variant="secondary">Offline</Badge>
                        )}
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{formatHandshake(p.last_handshake)}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {formatBytes(p.rx_bytes)} / {formatBytes(p.tx_bytes)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ icon, label, value, valueClass }: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center gap-2 text-muted-foreground mb-1">
          {icon}
          <span className="text-xs">{label}</span>
        </div>
        <p className={`text-2xl font-bold ${valueClass ?? ""}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
