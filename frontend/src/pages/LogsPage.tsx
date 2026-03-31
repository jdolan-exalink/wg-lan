import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionLogsApi } from "@/api/connection-logs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw, AlertTriangle, AlertCircle, Info, XCircle, ChevronDown, ChevronRight, Activity } from "lucide-react";
import type { ConnectionLog } from "@/types/connection-log";

const severityConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  info: { icon: <Info className="h-4 w-4" />, color: "text-blue-400", label: "Info" },
  warning: { icon: <AlertTriangle className="h-4 w-4" />, color: "text-yellow-400", label: "Warning" },
  error: { icon: <AlertCircle className="h-4 w-4" />, color: "text-orange-400", label: "Error" },
  critical: { icon: <XCircle className="h-4 w-4" />, color: "text-red-400", label: "Critical" },
};

const eventTypeLabels: Record<string, string> = {
  handshake: "Handshake",
  disconnect: "Disconnect",
  timeout: "Timeout",
  firewall_block: "Firewall Block",
  config_applied: "Config Applied",
  interface_up: "Interface Up",
  interface_down: "Interface Down",
  error: "Error",
};

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
              expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />
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
            {log.peer_name && (
              <span className="font-medium text-sm">{log.peer_name}</span>
            )}
            {log.peer_ip && (
              <span className="text-xs font-mono text-muted-foreground">{log.peer_ip}</span>
            )}
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
              <p className="text-xs text-muted-foreground font-medium">Details:</p>
              <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                {JSON.stringify(JSON.parse(log.details!), null, 2)}
              </pre>
              {log.source_ip && (
                <p className="text-xs text-muted-foreground">
                  Source: <code className="font-mono">{log.source_ip}</code>
                </p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export function LogsPage() {
  const qc = useQueryClient();
  const [filterEventType, setFilterEventType] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [limit, setLimit] = useState(100);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["connection-logs", filterEventType, filterSeverity, limit],
    queryFn: () => {
      const params: Record<string, any> = { limit };
      if (filterEventType !== "all") params.event_type = filterEventType;
      if (filterSeverity !== "all") params.severity = filterSeverity;
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
                <p className="text-xs text-muted-foreground">Total Events</p>
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
                <p className="text-xs text-muted-foreground">Errors (24h)</p>
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
                <p className="text-xs text-muted-foreground">Critical</p>
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
                <p className="text-xs text-muted-foreground">Peers with Errors</p>
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
              Peers with Recent Errors
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Peer</th>
                  <th className="text-left px-4 py-2 font-medium">Error Count</th>
                  <th className="text-left px-4 py-2 font-medium">Last Error</th>
                  <th className="text-left px-4 py-2 font-medium">Message</th>
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Select value={filterEventType} onValueChange={setFilterEventType}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Event Type" />
            </SelectTrigger>
            <SelectContent>
              {eventTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type === "all" ? "All Types" : eventTypeLabels[type] || type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterSeverity} onValueChange={setFilterSeverity}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              {severities.map((sev) => (
                <SelectItem key={sev} value={sev}>
                  {sev === "all" ? "All Severities" : severityConfig[sev]?.label || sev}
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
          Sync Status
        </Button>
      </div>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Connection Logs</CardTitle>
          <CardDescription>
            {logs.length} events — auto-refresh every 15s
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="w-8 px-4 py-2" />
                <th className="text-left px-4 py-2 font-medium">Timestamp</th>
                <th className="text-left px-4 py-2 font-medium">Event</th>
                <th className="text-left px-4 py-2 font-medium">Severity</th>
                <th className="text-left px-4 py-2 font-medium">Peer</th>
                <th className="text-left px-4 py-2 font-medium">Message</th>
                <th className="text-left px-4 py-2 font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">No logs yet</td></tr>
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
