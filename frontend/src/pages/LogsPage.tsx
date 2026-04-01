import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionLogsApi } from "@/api/connection-logs";
import { peersApi } from "@/api/peers";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RefreshCw,
  AlertTriangle,
  AlertCircle,
  Info,
  XCircle,
  ChevronDown,
  ChevronRight,
  Activity,
  CheckCircle2,
  Shield,
  ShieldCheck,
  ShieldX,
  Network,
  Router,
  Globe,
} from "lucide-react";
import type { ConnectionLog } from "@/types/connection-log";
import type { Peer } from "@/types/peer";

// ─── Severity config ──────────────────────────────────────────────────────────

const severityConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  info:     { icon: <Info     className="h-4 w-4" />, color: "text-blue-400",   label: "Info"     },
  warning:  { icon: <AlertTriangle className="h-4 w-4" />, color: "text-yellow-400", label: "Warning"  },
  error:    { icon: <AlertCircle   className="h-4 w-4" />, color: "text-orange-400", label: "Error"    },
  critical: { icon: <XCircle       className="h-4 w-4" />, color: "text-red-400",    label: "Critical" },
};

const eventTypeLabels: Record<string, string> = {
  handshake:        "Handshake",
  disconnect:       "Desconexión",
  timeout:          "Timeout",
  firewall_block:   "Bloqueo Firewall",
  config_applied:   "Config Aplicada",
  interface_up:     "Interfaz Arriba",
  interface_down:   "Interfaz Abajo",
  error:            "Error",
  policy_compiled:  "Políticas Compiladas",
  iptables_applied: "iptables Aplicado",
};

// ─── Log row (expandable) ─────────────────────────────────────────────────────

function LogRow({ log }: { log: ConnectionLog }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails = log.details && log.details !== "null";
  const severity = severityConfig[log.severity] || severityConfig.info;

  return (
    <>
      <tr
        className="border-b last:border-0 hover:bg-muted/20 cursor-pointer"
        onClick={() => hasDetails && setExpanded(!expanded)}
      >
        <td className="px-4 py-2">
          <div className="flex items-center gap-2">
            {hasDetails ? (
              expanded
                ? <ChevronDown  className="h-4 w-4 text-muted-foreground" />
                : <ChevronRight className="h-4 w-4 text-muted-foreground" />
            ) : (
              <span className="w-4" />
            )}
            <span className={severity.color}>{severity.icon}</span>
          </div>
        </td>
        <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
          {new Date(log.timestamp).toLocaleString()}
        </td>
        <td className="px-4 py-2">
          <Badge variant="outline" className="text-xs">
            {eventTypeLabels[log.event_type] || log.event_type}
          </Badge>
        </td>
        <td className="px-4 py-2">
          <Badge
            variant={log.severity === "critical" ? "destructive" : log.severity === "error" ? "default" : "secondary"}
            className="text-xs"
          >
            {severity.label}
          </Badge>
        </td>
        <td className="px-4 py-2">
          <div className="flex items-center gap-2">
            {log.peer_name && <span className="font-medium text-sm">{log.peer_name}</span>}
            {log.peer_ip   && <span className="text-xs font-mono text-muted-foreground">{log.peer_ip}</span>}
          </div>
        </td>
        <td className="px-4 py-2 text-sm max-w-md truncate">{log.message}</td>
        <td className="px-4 py-2 text-xs text-muted-foreground">
          {log.duration_ms ? `${log.duration_ms}ms` : "—"}
        </td>
      </tr>
      {expanded && hasDetails && (
        <tr className="bg-muted/10">
          <td colSpan={7} className="px-4 py-2">
            <div className="ml-6 space-y-2">
              <p className="text-xs text-muted-foreground font-medium">Detalles:</p>
              <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                {JSON.stringify(JSON.parse(log.details!), null, 2)}
              </pre>
              {log.source_ip && (
                <p className="text-xs text-muted-foreground">
                  Origen: <code className="font-mono">{log.source_ip}</code>
                </p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ─── Tab: Eventos de conexión ─────────────────────────────────────────────────

function ConnectionLogsTab() {
  const qc = useQueryClient();
  const [filterEventType, setFilterEventType] = useState<string>("all");
  const [filterSeverity,  setFilterSeverity]  = useState<string>("all");
  const [limit,           setLimit]           = useState(100);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["connection-logs", filterEventType, filterSeverity, limit],
    queryFn: () => {
      const params: Record<string, unknown> = { limit };
      if (filterEventType !== "all") params.event_type = filterEventType;
      if (filterSeverity  !== "all") params.severity   = filterSeverity;
      return connectionLogsApi.list(params).then((r) => r.data);
    },
    refetchInterval: 15_000,
  });

  const { data: stats } = useQuery({
    queryKey: ["connection-stats"],
    queryFn: () => connectionLogsApi.stats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const sync = useMutation({
    mutationFn: () => connectionLogsApi.sync(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["connection-logs"] });
      qc.invalidateQueries({ queryKey: ["connection-stats"] });
    },
  });

  const eventTypes = ["all", ...Object.keys(eventTypeLabels)];
  const severities = ["all", "info", "warning", "error", "critical"];

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Total Eventos</p>
                <p className="text-2xl font-bold">{stats?.total_events ?? 0}</p>
              </div>
              <Activity className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Errores (24h)</p>
                <p className="text-2xl font-bold text-destructive">
                  {stats?.events_by_severity?.error ?? 0}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Críticos</p>
                <p className="text-2xl font-bold text-destructive">
                  {stats?.events_by_severity?.critical ?? 0}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-destructive" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Peers con Errores</p>
                <p className="text-2xl font-bold text-orange-400">
                  {stats?.peers_with_errors?.length ?? 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Peers with Errors */}
      {stats?.peers_with_errors && stats.peers_with_errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-400" />
              Peers con Errores Recientes
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Peer</th>
                  <th className="text-left px-4 py-2 font-medium">Errores</th>
                  <th className="text-left px-4 py-2 font-medium">Último error</th>
                  <th className="text-left px-4 py-2 font-medium">Mensaje</th>
                </tr>
              </thead>
              <tbody>
                {stats.peers_with_errors.map((peer) => (
                  <tr key={peer.peer_id} className="border-b last:border-0">
                    <td className="px-4 py-2 font-medium">{peer.peer_name}</td>
                    <td className="px-4 py-2">
                      <Badge variant="destructive">{peer.error_count}</Badge>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {new Date(peer.last_error).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-xs max-w-md truncate">{peer.last_message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3 flex-wrap">
          <Select value={filterEventType} onValueChange={setFilterEventType}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Tipo de Evento" />
            </SelectTrigger>
            <SelectContent>
              {eventTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type === "all" ? "Todos los tipos" : eventTypeLabels[type] || type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterSeverity} onValueChange={setFilterSeverity}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Severidad" />
            </SelectTrigger>
            <SelectContent>
              {severities.map((sev) => (
                <SelectItem key={sev} value={sev}>
                  {sev === "all" ? "Todas" : severityConfig[sev]?.label || sev}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(limit)} onValueChange={(v) => setLimit(Number(v))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="50">50 logs</SelectItem>
              <SelectItem value="100">100 logs</SelectItem>
              <SelectItem value="250">250 logs</SelectItem>
              <SelectItem value="500">500 logs</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${sync.isPending ? "animate-spin" : ""}`} />
          Sincronizar
        </Button>
      </div>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Registro de Eventos</CardTitle>
          <CardDescription>
            {logs.length} eventos — actualización automática cada 15s
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="w-8 px-4 py-2" />
                <th className="text-left px-4 py-2 font-medium">Timestamp</th>
                <th className="text-left px-4 py-2 font-medium">Evento</th>
                <th className="text-left px-4 py-2 font-medium">Severidad</th>
                <th className="text-left px-4 py-2 font-medium">Peer</th>
                <th className="text-left px-4 py-2 font-medium">Mensaje</th>
                <th className="text-left px-4 py-2 font-medium">Duración</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Cargando...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Sin logs aún</td></tr>
              ) : (
                logs.map((log) => <LogRow key={log.id} log={log} />)
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Tab: Firewall Rules & Policies ──────────────────────────────────────────

function FirewallRulesTab({ logs }: { logs: ConnectionLog[] }) {
  const firewallLogs = logs.filter(
    (l) =>
      l.event_type === "policy_compiled" ||
      l.event_type === "iptables_applied" ||
      l.event_type === "firewall_block"
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Reglas de Firewall y Políticas
          </CardTitle>
          <CardDescription>
            Resultados de compilación de políticas y reglas iptables aplicadas
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="w-8 px-4 py-2" />
                <th className="text-left px-4 py-2 font-medium">Estado</th>
                <th className="text-left px-4 py-2 font-medium">Tipo</th>
                <th className="text-left px-4 py-2 font-medium">Origen</th>
                <th className="text-left px-4 py-2 font-medium">Destino</th>
                <th className="text-left px-4 py-2 font-medium">Mensaje</th>
                <th className="text-left px-4 py-2 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {firewallLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Sin eventos de firewall registrados aún
                  </td>
                </tr>
              ) : (
                firewallLogs.slice(0, 50).map((log) => {
                  const isBlocked =
                    log.severity === "warning" || log.event_type === "firewall_block";
                  const isOk = log.severity === "info" && log.event_type !== "firewall_block";
                  const details = log.details
                    ? (() => { try { return JSON.parse(log.details!); } catch { return null; } })()
                    : null;

                  return (
                    <tr key={log.id} className="border-b last:border-0 hover:bg-muted/20">
                      <td className="px-4 py-2">
                        {isBlocked ? (
                          <ShieldX className="h-4 w-4 text-red-500" />
                        ) : isOk ? (
                          <ShieldCheck className="h-4 w-4 text-green-500" />
                        ) : (
                          <Shield className="h-4 w-4 text-blue-400" />
                        )}
                      </td>
                      <td className="px-4 py-2">
                        <Badge
                          variant={isBlocked ? "destructive" : isOk ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {isBlocked ? "BLOQUEADO" : isOk ? "OK" : "INFO"}
                        </Badge>
                      </td>
                      <td className="px-4 py-2">
                        <Badge variant="outline" className="text-xs">
                          {eventTypeLabels[log.event_type] || log.event_type}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {details?.source || log.peer_ip || "—"}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {details?.destination || details?.dest || "—"}
                      </td>
                      <td className="px-4 py-2 text-sm max-w-xs truncate">
                        {log.message}
                      </td>
                      <td className="px-4 py-2 text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Tab: Branch Office Routes ────────────────────────────────────────────────

function BranchOfficeRoutesTab() {
  const { data: peers = [], isLoading } = useQuery({
    queryKey: ["peers", "branch_office"],
    queryFn: () => peersApi.list("branch_office").then((r) => r.data),
    refetchInterval: 30_000,
  });

  const branchPeers = (peers as Peer[]).filter(
    (p) => p.peer_type === "branch_office" && p.remote_subnets && p.remote_subnets.length > 0
  );

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Branch Offices</p>
                <p className="text-2xl font-bold">{branchPeers.length}</p>
              </div>
              <Router className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Subredes Totales</p>
                <p className="text-2xl font-bold">
                  {branchPeers.reduce((acc, p) => acc + p.remote_subnets.length, 0)}
                </p>
              </div>
              <Network className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Activos Online</p>
                <p className="text-2xl font-bold text-green-500">
                  {branchPeers.filter((p) => p.is_enabled && p.is_online).length}
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Routes table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Rutas hacia Subredes de Branch Offices
          </CardTitle>
          <CardDescription>
            Subnets remotas de cada peer branch office — estas rutas se inyectan en AllowedIPs de los peers que tienen acceso
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">Cargando...</p>
          ) : branchPeers.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              No hay branch offices con subredes configuradas
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Branch Office</th>
                  <th className="text-left px-4 py-2 font-medium">IP VPN</th>
                  <th className="text-left px-4 py-2 font-medium">Estado</th>
                  <th className="text-left px-4 py-2 font-medium">Subredes Remotas (Rutas)</th>
                  <th className="text-left px-4 py-2 font-medium">Dispositivo</th>
                </tr>
              </thead>
              <tbody>
                {branchPeers.map((peer) => (
                  <tr key={peer.id} className="border-b last:border-0 hover:bg-muted/20">
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-2">
                        <Router className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{peer.name}</span>
                        {!peer.is_enabled && (
                          <Badge variant="secondary" className="text-xs">Desactivado</Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                      {peer.assigned_ip.split("/")[0]}
                    </td>
                    <td className="px-4 py-2">
                      {peer.is_online ? (
                        <div className="flex items-center gap-1.5">
                          <span className="h-2 w-2 rounded-full bg-green-500 inline-block" />
                          <span className="text-xs text-green-500">Online</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <span className="h-2 w-2 rounded-full bg-muted-foreground inline-block" />
                          <span className="text-xs text-muted-foreground">Offline</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex flex-wrap gap-1.5">
                        {peer.remote_subnets.map((subnet, i) => (
                          <Badge key={i} variant="outline" className="font-mono text-xs px-2 py-0.5">
                            {subnet}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground capitalize">
                      {peer.device_type ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Per-peer expanded detail cards */}
      {branchPeers.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {branchPeers.map((peer) => (
            <Card key={peer.id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Router className="h-4 w-4" />
                  {peer.name}
                  <Badge
                    variant={peer.is_online ? "default" : "secondary"}
                    className="text-xs ml-auto"
                  >
                    {peer.is_online ? "Online" : "Offline"}
                  </Badge>
                </CardTitle>
                <CardDescription className="font-mono text-xs">
                  {peer.assigned_ip.split("/")[0]}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-xs text-muted-foreground mb-2">
                  Rutas propagadas a peers con acceso a este branch:
                </p>
                <div className="space-y-1">
                  {peer.remote_subnets.map((subnet, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 rounded bg-muted/40 px-3 py-1.5"
                    >
                      <Network className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <code className="text-xs font-mono">{subnet}</code>
                      <span className="ml-auto text-xs text-muted-foreground">
                        via {peer.assigned_ip.split("/")[0]}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function LogsPage() {
  const { data: allLogs = [] } = useQuery({
    queryKey: ["connection-logs-firewall"],
    queryFn: () => connectionLogsApi.list({ limit: 200 }).then((r) => r.data),
    refetchInterval: 20_000,
  });

  return (
    <div className="space-y-4">
      <Tabs defaultValue="events">
        <TabsList className="mb-2">
          <TabsTrigger value="events" className="flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            Eventos de Conexión
          </TabsTrigger>
          <TabsTrigger value="firewall" className="flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5" />
            Firewall &amp; Políticas
          </TabsTrigger>
          <TabsTrigger value="routes" className="flex items-center gap-1.5">
            <Network className="h-3.5 w-3.5" />
            Rutas Branch Office
          </TabsTrigger>
        </TabsList>

        <TabsContent value="events">
          <ConnectionLogsTab />
        </TabsContent>

        <TabsContent value="firewall">
          <FirewallRulesTab logs={allLogs} />
        </TabsContent>

        <TabsContent value="routes">
          <BranchOfficeRoutesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
