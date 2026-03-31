import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatBytes, formatHandshake } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const POLL_INTERVAL = 10_000;

function StatCard({ icon, label, value, valueClass }: { icon: React.ReactNode; label: string; value: string | number; valueClass?: string }) {
  return (
    <div className="bg-surface-container p-6 rounded-xl flex flex-col justify-between hover:bg-surface-container-high transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <span className="font-label text-xs uppercase tracking-widest text-outline">{label}</span>
        <div className="p-2 rounded-lg bg-primary-container/10 text-primary">
          {icon}
        </div>
      </div>
      <div>
        <h3 className={`text-4xl font-bold font-headline mb-1 ${valueClass ?? "text-on-surface"}`}>{value}</h3>
      </div>
    </div>
  );
}

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
      {/* High Level Stats Bento Grid */}
      <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
        <StatCard
          icon={<span className="material-symbols-outlined">hub</span>}
          label="Total Peers"
          value={stats?.total_peers ?? "—"}
        />
        <StatCard
          icon={<span className="material-symbols-outlined text-tertiary">online_prediction</span>}
          label="Active Nodes"
          value={stats?.online_peers ?? "—"}
          valueClass="text-tertiary"
        />
        <StatCard
          icon={<span className="material-symbols-outlined text-error">warning</span>}
          label="Offline"
          value={stats?.offline_peers ?? "—"}
          valueClass="text-error"
        />
        <div className="bg-surface-container p-6 rounded-xl flex flex-col justify-between hover:bg-surface-container-high transition-colors kinetic-gradient shadow-2xl shadow-primary-container/20">
          <div className="flex justify-between items-start mb-4">
            <span className="font-label text-xs uppercase tracking-widest text-on-primary-container">Total Traffic</span>
            <div className="p-2 rounded-lg bg-white/10 text-white">
              <span className="material-symbols-outlined">speed</span>
            </div>
          </div>
          <div className="text-on-primary-container">
            <h3 className="text-4xl font-bold font-headline mb-1">
              {stats ? formatBytes(stats.total_rx_bytes + stats.total_tx_bytes) : "—"}
            </h3>
          </div>
        </div>
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Traffic Chart */}
        <div className="lg:col-span-2 bg-surface-container-low rounded-xl p-8">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h4 className="font-headline font-bold text-lg text-on-surface">Top Peers by Traffic</h4>
              <p className="text-sm text-outline">Throughput distribution across top peers</p>
            </div>
          </div>
          {topTraffic.length === 0 ? (
            <p className="text-sm text-outline py-8 text-center">No traffic data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={256}>
              <BarChart data={topTraffic} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#928ea1" }} />
                <YAxis tick={{ fontSize: 11, fill: "#928ea1" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1d1c3c", border: "1px solid #474555", borderRadius: "8px" }}
                  formatter={(v: number) => [`${v} KB`, ""]}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: "#928ea1" }} />
                <Bar dataKey="RX" fill="#624af4" radius={[3, 3, 0, 0]} />
                <Bar dataKey="TX" fill="#00daf3" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Health Snapshot */}
        <div className="bg-surface-container-low rounded-xl p-8 relative overflow-hidden">
          <div className="absolute -right-12 -top-12 w-48 h-48 bg-primary/5 rounded-full blur-3xl" />
          <h4 className="font-headline font-bold text-lg mb-6 text-on-surface">Global Health</h4>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-xs font-label uppercase mb-2">
                <span className="text-outline">Peers Online</span>
                <span className="text-tertiary">{stats?.online_peers ?? 0} / {stats?.total_peers ?? 0}</span>
              </div>
              <div className="h-1 bg-surface-container-highest rounded-full">
                <div
                  className="h-full bg-tertiary rounded-full transition-all duration-500"
                  style={{ width: stats?.total_peers ? `${(stats.online_peers / stats.total_peers) * 100}%` : "0%" }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs font-label uppercase mb-2">
                <span className="text-outline">RoadWarriors</span>
                <span className="text-primary">{stats?.roadwarrior_count ?? 0}</span>
              </div>
              <div className="h-1 bg-surface-container-highest rounded-full">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: stats?.total_peers ? `${(stats.roadwarrior_count / stats.total_peers) * 100}%` : "0%" }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs font-label uppercase mb-2">
                <span className="text-outline">Branch Offices</span>
                <span className="text-on-surface">{stats?.branch_office_count ?? 0}</span>
              </div>
              <div className="h-1 bg-surface-container-highest rounded-full">
                <div
                  className="h-full bg-on-surface rounded-full transition-all duration-500"
                  style={{ width: stats?.total_peers ? `${(stats.branch_office_count / stats.total_peers) * 100}%` : "0%" }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Peer Status Table */}
      <Card className="bg-surface-container rounded-xl overflow-hidden">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium font-headline text-on-surface">Active Peer List</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-surface-container-high/50 font-label text-[10px] uppercase tracking-[0.15em] text-outline">
                  <th className="text-left px-6 py-4 font-semibold">Name</th>
                  <th className="text-left px-6 py-4 font-semibold">Type</th>
                  <th className="text-left px-6 py-4 font-semibold">IP</th>
                  <th className="text-left px-6 py-4 font-semibold">Status</th>
                  <th className="text-left px-6 py-4 font-semibold">Handshake</th>
                  <th className="text-left px-6 py-4 font-semibold">RX / TX</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/5">
                {peerStatuses.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-outline">
                      <div className="flex flex-col items-center gap-3">
                        <span className="material-symbols-outlined text-4xl text-outline/30">hub</span>
                        <p className="font-headline text-lg">No peers yet</p>
                        <p className="text-sm">Create your first peer to get started</p>
                      </div>
                    </td>
                  </tr>
                ) : peerStatuses.map((p) => (
                  <tr key={p.id} className="hover:bg-surface-container-high transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                          <span className="material-symbols-outlined text-sm text-outline">
                            {p.peer_type === "branch_office" ? "router" : "laptop_mac"}
                          </span>
                        </div>
                        <span className="font-semibold text-sm text-on-surface">{p.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-label text-xs text-outline capitalize">{p.peer_type.replace("_", " ")}</td>
                    <td className="px-6 py-4 font-label text-xs text-primary font-mono">{p.assigned_ip}</td>
                    <td className="px-6 py-4">
                      <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-tertiary-container/10 border border-tertiary/10">
                        <span className={`w-1.5 h-1.5 rounded-full ${p.is_online ? "bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]" : "bg-error"}`} />
                        <span className="text-[10px] font-label font-bold uppercase text-tertiary">
                          {p.is_online ? "Online" : "Offline"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-label text-xs text-outline">{formatHandshake(p.last_handshake)}</td>
                    <td className="px-6 py-4 font-label text-xs">
                      <span className="text-tertiary">{formatBytes(p.rx_bytes)}</span>
                      {" / "}
                      <span className="text-outline">{formatBytes(p.tx_bytes)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
