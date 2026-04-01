import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { formatBytes, formatHandshake } from "@/lib/utils";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from "recharts";
import {
  Laptop,
  Smartphone,
  Router,
  Server,
  Building2,
  Activity,
  Users,
  WifiOff,
  Database,
} from "lucide-react";
import type { PeerType } from "@/types/peer";

const POLL_INTERVAL = 10_000;

// ── Bandwidth history point ──────────────────────
interface BwPoint {
  t: string;
  rx: number; // bytes/s
  tx: number; // bytes/s
}

// ── Device icon resolution ───────────────────────
function DeviceIcon({ peerType, name, className }: { peerType: PeerType; name: string; className?: string }) {
  const n = name.toLowerCase();

  if (peerType === "branch_office") {
    return n.includes("router") || n.includes("mkt") || n.includes("rb")
      ? <Router className={className} />
      : <Building2 className={className} />;
  }

  if (peerType === "server") return <Server className={className} />;

  // Road warrior — heuristic from name
  if (n.includes("iphone") || n.includes("ios") || n.includes("android") || n.includes("pixel") || n.includes("phone"))
    return <Smartphone className={className} />;
  if (n.includes("server") || n.includes("srv") || n.includes("vps"))
    return <Server className={className} />;

  return <Laptop className={className} />;
}

// ── Stat card ────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  accent?: "blue" | "green" | "red" | "gradient";
}) {
  const valueColor =
    accent === "green"
      ? "text-tertiary"
      : accent === "red"
        ? "text-error"
        : accent === "blue"
          ? "text-primary"
          : "text-on-surface";

  const iconBg =
    accent === "green"
      ? "bg-tertiary-container/20 text-tertiary"
      : accent === "red"
        ? "bg-error-container/20 text-error"
        : accent === "blue"
          ? "bg-primary-container/10 text-primary"
          : "bg-primary-container/10 text-primary";

  if (accent === "gradient") {
    return (
      <div className="kinetic-gradient p-5 rounded-xl flex flex-col gap-3 kinetic-glow">
        <div className="flex justify-between items-start">
          <span className="font-label text-[11px] uppercase tracking-widest text-on-primary-container/80">
            {label}
          </span>
          <div className="p-1.5 rounded-lg bg-white/10 text-white">
            {icon}
          </div>
        </div>
        <span className="text-3xl font-bold font-headline text-white leading-none">{value}</span>
      </div>
    );
  }

  return (
    <div className="bg-surface-container p-5 rounded-xl flex flex-col gap-3 hover:bg-surface-container-high transition-colors border border-outline-variant/10">
      <div className="flex justify-between items-start">
        <span className="font-label text-[11px] uppercase tracking-widest text-outline">{label}</span>
        <div className={`p-1.5 rounded-lg ${iconBg}`}>{icon}</div>
      </div>
      <span className={`text-3xl font-bold font-headline leading-none ${valueColor}`}>{value}</span>
    </div>
  );
}

// ── Custom tooltip for area chart ────────────────
function BwTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-container-highest border border-outline-variant/20 rounded-lg px-3 py-2 text-xs font-label shadow-xl">
      <p className="text-outline mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {formatBytes(p.value)}/s
        </p>
      ))}
    </div>
  );
}

// ── Main page ────────────────────────────────────
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

  // ── Real-time bandwidth accumulator ─────────────
  const prevRef = useRef<{ rx: number; tx: number; ts: number } | null>(null);
  const [bwHistory, setBwHistory] = useState<BwPoint[]>([]);

  useEffect(() => {
    if (!traffic.length) return;
    const totalRx = traffic.reduce((s, t) => s + t.rx_bytes, 0);
    const totalTx = traffic.reduce((s, t) => s + t.tx_bytes, 0);
    const now = Date.now();

    if (prevRef.current) {
      const dt = (now - prevRef.current.ts) / 1000;
      if (dt > 0.5) {
        const rx = Math.max(0, (totalRx - prevRef.current.rx) / dt);
        const tx = Math.max(0, (totalTx - prevRef.current.tx) / dt);
        const t = new Date(now).toLocaleTimeString("en", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
        setBwHistory((prev) => [...prev.slice(-23), { t, rx, tx }]);
      }
    }
    prevRef.current = { rx: totalRx, tx: totalTx, ts: now };
  }, [traffic]);

  // ── Top peers bar chart data ─────────────────────
  const topTraffic = traffic.slice(0, 8).map((t) => ({
    name: t.peer_name.length > 12 ? t.peer_name.slice(0, 12) + "…" : t.peer_name,
    RX: Math.round(t.rx_bytes / 1024),
    TX: Math.round(t.tx_bytes / 1024),
  }));

  // ── Current BW (last point) ──────────────────────
  const latestBw = bwHistory[bwHistory.length - 1];

  return (
    <div className="space-y-5">
      {/* ── Stat cards ────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          icon={<Users className="w-4 h-4" />}
          label="Total Peers"
          value={stats?.total_peers ?? "—"}
        />
        <StatCard
          icon={<Activity className="w-4 h-4" />}
          label="Active Nodes"
          value={stats?.online_peers ?? "—"}
          accent="green"
        />
        <StatCard
          icon={<WifiOff className="w-4 h-4" />}
          label="Offline"
          value={stats?.offline_peers ?? "—"}
          accent="red"
        />
        <StatCard
          icon={<Database className="w-4 h-4" />}
          label="Total Traffic"
          value={stats ? formatBytes(stats.total_rx_bytes + stats.total_tx_bytes) : "—"}
          accent="gradient"
        />
      </div>

      {/* ── Live bandwidth chart ───────────────────── */}
      <div className="bg-surface-container rounded-xl border border-outline-variant/10 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-headline font-semibold text-sm text-on-surface">Live Bandwidth</h4>
            <p className="text-[11px] text-outline mt-0.5 font-label">Aggregate RX / TX · updates every 10 s</p>
          </div>
          {latestBw && (
            <div className="flex items-center gap-4 text-xs font-label">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-primary inline-block" />
                <span className="text-outline">RX</span>
                <span className="text-on-surface font-semibold">{formatBytes(latestBw.rx)}/s</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-tertiary inline-block" />
                <span className="text-outline">TX</span>
                <span className="text-on-surface font-semibold">{formatBytes(latestBw.tx)}/s</span>
              </span>
            </div>
          )}
        </div>

        {bwHistory.length < 2 ? (
          <div className="h-36 flex items-center justify-center text-outline text-xs font-label">
            <span className="flex items-center gap-2">
              <Activity className="w-4 h-4 animate-pulse" />
              Collecting data… (requires ≥ 2 poll cycles)
            </span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={144}>
            <AreaChart data={bwHistory} margin={{ top: 4, right: 0, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id="rxGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="rgb(var(--c-primary))" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="rgb(var(--c-primary))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="txGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="rgb(var(--c-success))" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="rgb(var(--c-success))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--c-border))" vertical={false} />
              <XAxis
                dataKey="t"
                tick={{ fontSize: 9, fill: "rgb(var(--c-muted))", fontFamily: "Space Grotesk" }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 9, fill: "rgb(var(--c-muted))", fontFamily: "Space Grotesk" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => (v >= 1024 ? `${Math.round(v / 1024)}K` : `${v}`)}
              />
              <Tooltip content={<BwTooltip />} />
              <Area
                type="monotone"
                dataKey="rx"
                name="RX"
                stroke="rgb(var(--c-primary))"
                strokeWidth={2}
                fill="url(#rxGrad)"
                dot={false}
                activeDot={{ r: 3 }}
              />
              <Area
                type="monotone"
                dataKey="tx"
                name="TX"
                stroke="rgb(var(--c-success))"
                strokeWidth={2}
                fill="url(#txGrad)"
                dot={false}
                activeDot={{ r: 3 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Analytics row ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Top Peers by Traffic */}
        <div className="lg:col-span-2 bg-surface-container rounded-xl border border-outline-variant/10 p-5">
          <h4 className="font-headline font-semibold text-sm text-on-surface mb-1">
            Top Peers by Traffic
          </h4>
          <p className="text-[11px] text-outline mb-4 font-label">Cumulative bytes · top 8 peers</p>
          {topTraffic.length === 0 ? (
            <p className="text-sm text-outline py-8 text-center">No traffic data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={topTraffic} margin={{ top: 0, right: 0, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--c-border))" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 10, fill: "rgb(var(--c-muted))", fontFamily: "Space Grotesk" }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "rgb(var(--c-muted))", fontFamily: "Space Grotesk" }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgb(var(--c-high))",
                    border: "1px solid rgb(var(--c-border))",
                    borderRadius: "8px",
                    fontSize: 11,
                    fontFamily: "Space Grotesk",
                    color: "rgb(var(--c-text))",
                  }}
                  formatter={(v: number) => [`${v} KB`, ""]}
                />
                <Legend
                  wrapperStyle={{ fontSize: 10, fontFamily: "Space Grotesk", color: "rgb(var(--c-muted))" }}
                />
                <Bar dataKey="RX" fill="rgb(var(--c-accent))" radius={[3, 3, 0, 0]} />
                <Bar dataKey="TX" fill="rgb(var(--c-success))" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Global Health */}
        <div className="bg-surface-container rounded-xl border border-outline-variant/10 p-5">
          <h4 className="font-headline font-semibold text-sm text-on-surface mb-4">Global Health</h4>
          <div className="space-y-5">
            {[
              {
                label: "Peers Online",
                value: stats?.online_peers ?? 0,
                total: stats?.total_peers ?? 0,
                color: "bg-tertiary",
                textColor: "text-tertiary",
              },
              {
                label: "RoadWarriors",
                value: stats?.roadwarrior_count ?? 0,
                total: stats?.total_peers ?? 0,
                color: "bg-primary",
                textColor: "text-primary",
              },
              {
                label: "Branch Offices",
                value: stats?.branch_office_count ?? 0,
                total: stats?.total_peers ?? 0,
                color: "bg-on-surface-variant",
                textColor: "text-on-surface-variant",
              },
            ].map(({ label, value, total, color, textColor }) => (
              <div key={label}>
                <div className="flex justify-between text-[11px] font-label mb-1.5">
                  <span className="text-outline uppercase tracking-wide">{label}</span>
                  <span className={textColor}>{value} / {total}</span>
                </div>
                <div className="h-1 bg-surface-container-highest rounded-full overflow-hidden">
                  <div
                    className={`h-full ${color} rounded-full transition-all duration-700`}
                    style={{ width: total > 0 ? `${(value / total) * 100}%` : "0%" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Peer status table ─────────────────────── */}
      <div className="bg-surface-container rounded-xl border border-outline-variant/10 overflow-hidden">
        <div className="px-5 py-4 border-b border-outline-variant/10">
          <h4 className="font-headline font-semibold text-sm text-on-surface">Active Peer List</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-container-high/40">
                {["Peer", "Type", "IP Address", "Status", "Last Handshake", "RX / TX"].map((h) => (
                  <th
                    key={h}
                    className="text-left px-5 py-3 font-label text-[10px] uppercase tracking-widest text-outline font-semibold"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/8">
              {peerStatuses.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-14 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center">
                        <Users className="w-6 h-6 text-outline/40" />
                      </div>
                      <p className="font-headline font-semibold text-on-surface">No peers yet</p>
                      <p className="text-xs text-outline">Create your first peer to get started</p>
                    </div>
                  </td>
                </tr>
              ) : (
                peerStatuses.map((p) => (
                  <tr
                    key={p.id}
                    className="hover:bg-surface-container-high/30 transition-colors"
                  >
                    {/* Peer name + icon */}
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surface-container-highest border border-outline-variant/10 flex items-center justify-center flex-shrink-0">
                          <DeviceIcon
                            peerType={p.peer_type}
                            name={p.name}
                            className="w-4 h-4 text-outline"
                          />
                        </div>
                        <span className="font-semibold text-[13px] text-on-surface">{p.name}</span>
                      </div>
                    </td>

                    {/* Type */}
                    <td className="px-5 py-3.5">
                      <span className="font-label text-[11px] text-outline capitalize">
                        {p.peer_type.replace("_", " ")}
                      </span>
                    </td>

                    {/* IP */}
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-[12px] text-primary bg-primary-container/8 px-2 py-0.5 rounded">
                        {p.assigned_ip}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-label font-semibold uppercase tracking-wide border ${
                          p.is_online
                            ? "bg-tertiary-container/15 text-tertiary border-tertiary/15"
                            : "bg-error-container/15 text-error border-error/15"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            p.is_online ? "bg-tertiary status-pulse" : "bg-error"
                          }`}
                        />
                        {p.is_online ? "Online" : "Offline"}
                      </span>
                    </td>

                    {/* Handshake */}
                    <td className="px-5 py-3.5">
                      <span className="font-label text-[11px] text-outline">
                        {formatHandshake(p.last_handshake)}
                      </span>
                    </td>

                    {/* Traffic */}
                    <td className="px-5 py-3.5">
                      <span className="font-label text-[11px]">
                        <span className="text-primary">{formatBytes(p.rx_bytes)}</span>
                        <span className="text-outline mx-1">/</span>
                        <span className="text-outline">{formatBytes(p.tx_bytes)}</span>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
