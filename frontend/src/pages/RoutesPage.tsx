import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { routesApi } from "@/api/routes";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Route, AlertTriangle } from "lucide-react";
import { isAxiosError } from "axios";

function errorText(error: unknown) {
  return isAxiosError(error) ? String(error.response?.data?.detail ?? error.message) : String(error);
}
const labels = { active: "Instalada", connected: "Conectada", missing: "Falta ruta", conflict: "Conflicto", unconfigured: "Sin gateway", disabled: "Deshabilitada" };

export function RoutesPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showLocal, setShowLocal] = useState(false);
  const query = useQuery({ queryKey: ["routes"], queryFn: () => routesApi.list().then(r => r.data), refetchInterval: 15000 });
  const reconcile = useMutation({ mutationFn: () => routesApi.reconcile(), onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["routes"] });
    qc.invalidateQueries({ queryKey: ["peers"] });
  }, onError: () => qc.invalidateQueries({ queryKey: ["routes"] }) });
  const expected = query.data?.expected ?? [];
  const issues = expected.filter(r => ["missing", "conflict", "unconfigured"].includes(r.status));
  const system = (query.data?.routes ?? []).filter(r => (showLocal || r.table !== "local") && `${r.destination} ${r.gateway ?? ""} ${r.interface ?? ""} ${r.table}`.toLowerCase().includes(search.toLowerCase()));
  return <div className="space-y-6">
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><CardTitle className="flex items-center gap-2"><Route className="h-5 w-5" />Rutas del servidor</CardTitle>
            <CardDescription>Las redes con gateway crean su ruta automáticamente. Esta vista compara la configuración con las rutas reales de Linux cada 15 segundos.</CardDescription></div>
          <div className="flex gap-2"><Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}><RefreshCw className="h-4 w-4" />Actualizar</Button>
            <Button onClick={() => reconcile.mutate()} disabled={reconcile.isPending}>{reconcile.isPending ? "Aplicando…" : "Reconciliar rutas"}</Button></div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{expected.length} redes registradas · {issues.length} pendientes. <Link to="/networks" className="text-primary underline">Configurar redes y gateways</Link></p>
        {query.isLoading && <p role="status">Consultando rutas…</p>}
        {query.error && <p role="alert" className="text-destructive">No se pudieron leer las rutas: {errorText(query.error)}</p>}
        {reconcile.error && <p role="alert" className="text-destructive">{errorText(reconcile.error)}</p>}
        {reconcile.isSuccess && <p role="status" className="text-green-600">Reconciliación finalizada. Revisá los estados pendientes.</p>}
        {query.data?.warnings.map(w => <p key={w} className="flex items-center gap-2 text-sm text-amber-600"><AlertTriangle className="h-4 w-4 shrink-0" />{w}</p>)}
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left">
          {["Red", "Destino", "Gateway", "Interfaz", "Estado"].map(t => <th key={t} className="p-3">{t}</th>)}</tr></thead><tbody>
          {expected.map(r => <tr key={r.network_id} className="border-b"><td className="p-3">{r.name}</td><td className="p-3 font-mono text-xs">{r.destination}</td><td className="p-3">{r.peer_name ?? r.gateway ?? "Directa / sin definir"}</td><td className="p-3 font-mono">{r.interface ?? "—"}</td><td className="p-3"><Badge title={r.message} variant={["active", "connected"].includes(r.status) ? "secondary" : "outline"}>{labels[r.status]}</Badge><p className="mt-1 text-xs text-muted-foreground">{r.message}</p></td></tr>)}
        </tbody></table></div>
      </CardContent>
    </Card>
    <Card><CardHeader><CardTitle>Rutas existentes en Linux</CardTitle><CardDescription>Incluye rutas de NetLoom, interfaces conectadas, Docker y otros servicios. La reconciliación sólo elimina rutas identificadas como propias.</CardDescription></CardHeader>
      <CardContent className="space-y-4"><div className="flex flex-wrap gap-4 items-center"><Input className="max-w-sm" aria-label="Buscar rutas" placeholder="Buscar destino, gateway o interfaz…" value={search} onChange={e => setSearch(e.target.value)} /><label className="flex gap-2 text-sm"><input type="checkbox" checked={showLocal} onChange={e => setShowLocal(e.target.checked)} />Incluir tabla local</label></div>
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left">{["Destino", "Gateway", "Interfaz", "Tabla", "Protocolo", "Métrica", "Origen"].map(t => <th className="p-3" key={t}>{t}</th>)}</tr></thead><tbody>{system.map((r, i) => <tr key={i} className="border-b"><td className="p-3 font-mono text-xs">{r.destination}</td><td className="p-3 font-mono text-xs">{r.gateway ?? "Directa"}</td><td className="p-3 font-mono">{r.interface ?? r.route_type}</td><td className="p-3">{r.table}</td><td className="p-3">{r.protocol}</td><td className="p-3">{r.metric ?? "—"}</td><td className="p-3">{r.managed ? <Badge>NetLoom</Badge> : "Sistema / otro servicio"}</td></tr>)}</tbody></table></div>
      </CardContent></Card>
  </div>;
}
