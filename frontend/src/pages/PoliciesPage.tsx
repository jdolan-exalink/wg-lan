import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { policiesApi, groupsApi, firewallApi } from "@/api/networks";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  ArrowRight,
  ArrowLeft,
  ArrowLeftRight,
  Check,
  X,
  Trash2,
  Shield,
  ShieldOff,
  ShieldCheck,
  Save,
  RotateCcw,
  RefreshCw,
  GripVertical,
  Info,
} from "lucide-react";
import type { Policy, PeerGroup } from "@/types/network";

// ─── Direction helpers ────────────────────────────────────────────────────────

const directionIcon = (d: string) =>
  d === "outbound" ? <ArrowRight className="h-3 w-3" /> :
  d === "inbound"  ? <ArrowLeft  className="h-3 w-3" /> :
                     <ArrowLeftRight className="h-3 w-3" />;

const directionLabel: Record<string, string> = {
  outbound: "→ Saliente",
  inbound:  "← Entrante",
  both:     "↔ Ambas",
};

// ─── Staged changes ───────────────────────────────────────────────────────────

type PendingOp = "create" | "update" | "delete";

interface StagedPolicy extends Policy {
  _pending?: PendingOp;
  _localId?: string;
}

// ─── Main component ───────────────────────────────────────────────────────────

export function PoliciesPage() {
  const qc = useQueryClient();

  // ── Server data ────────────────────────────────────────────────────────────
  // NOTE: do NOT use a = [] default here — that creates a new reference every render
  // and makes the sync useEffect loop infinitely while the query is loading.
  const { data: serverPolicies, isLoading: policiesLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: () => policiesApi.list().then((r) => r.data),
  });

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const { data: firewallStatus } = useQuery({
    queryKey: ["firewall-status"],
    queryFn: () => firewallApi.getStatus().then((r) => r.data),
  });

  const { data: fwRules = [], refetch: refetchRules } = useQuery({
    queryKey: ["firewall-rules"],
    queryFn: () => policiesApi.firewallRules().then((r) => r.data),
    refetchInterval: 10_000,
  });

  // ── Staged state ────────────────────────────────────────────────────────────
  const [stagedPolicies, setStagedPolicies] = useState<StagedPolicy[]>([]);
  const [stagedFirewall, setStagedFirewall] = useState<boolean | null>(null);
  const [positionsChanged, setPositionsChanged] = useState(false);

  // ── Drag-and-drop state ─────────────────────────────────────────────────────
  const [dragSrcIdx, setDragSrcIdx] = useState<number | null>(null);
  const [dragOverIdx, setDragOverIdx] = useState<number | null>(null);

  // Sync staged to server state when server data changes
  useEffect(() => {
    if (serverPolicies !== undefined) {
      setStagedPolicies(serverPolicies.map((p) => ({ ...p })));
    }
  }, [serverPolicies]);

  useEffect(() => {
    if (firewallStatus !== undefined && stagedFirewall === null) {
      setStagedFirewall(firewallStatus.firewall_enabled);
    }
  }, [firewallStatus]);

  // ── Derived ─────────────────────────────────────────────────────────────────
  const firewallOn = stagedFirewall ?? firewallStatus?.firewall_enabled ?? false;

  const hasPendingChanges =
    stagedPolicies.some((p) => p._pending) ||
    positionsChanged ||
    (stagedFirewall !== null && stagedFirewall !== firewallStatus?.firewall_enabled);

  const visiblePolicies = stagedPolicies.filter((p) => p._pending !== "delete");

  // ── Drag handlers (for rule reordering) ─────────────────────────────────────
  const handleDragStart = (e: React.DragEvent, idx: number) => {
    e.dataTransfer.effectAllowed = "move";
    setDragSrcIdx(idx);
  };
  const handleDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverIdx(idx);
  };
  const handleDragLeave = () => setDragOverIdx(null);
  const handleDrop = (e: React.DragEvent, dstIdx: number) => {
    e.preventDefault();
    setDragOverIdx(null);
    if (dragSrcIdx === null || dragSrcIdx === dstIdx) { setDragSrcIdx(null); return; }
    const vis = [...visiblePolicies];
    const [moved] = vis.splice(dragSrcIdx, 1);
    vis.splice(dstIdx, 0, moved);
    const deleted = stagedPolicies.filter((p) => p._pending === "delete");
    setStagedPolicies([...vis, ...deleted]);
    setPositionsChanged(true);
    setDragSrcIdx(null);
  };
  const handleDragEnd = () => { setDragSrcIdx(null); setDragOverIdx(null); };

  // ── Add-rule form state ─────────────────────────────────────────────────────
  const [showForm, setShowForm]       = useState(false);
  const [newSource, setNewSource]     = useState("");
  const [newDest, setNewDest]         = useState("");
  const [newDir, setNewDir]           = useState<"outbound" | "inbound" | "both">("both");
  const [newAction, setNewAction]     = useState<"allow" | "deny">("allow");

  // ── Mutations ───────────────────────────────────────────────────────────────
  const setFirewallMutation = useMutation({
    mutationFn: (enabled: boolean) => firewallApi.setStatus(enabled),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["firewall-status"] }),
  });

  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof policiesApi.create>[0]) => policiesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof policiesApi.update>[1] }) =>
      policiesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => policiesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  // ── Staged actions ──────────────────────────────────────────────────────────
  const stageAddRule = () => {
    if (!newSource || !newDest) return;
    const localId = `new-${Date.now()}`;
    const sourceGroup = (groups ?? []).find((g: PeerGroup) => g.id === parseInt(newSource));
    const destGroup   = (groups ?? []).find((g: PeerGroup) => g.id === parseInt(newDest));
    const staged: StagedPolicy = {
      id: -1,
      _localId: localId,
      _pending: "create",
      source_group_id:   parseInt(newSource),
      source_group_name: sourceGroup?.name ?? null,
      dest_group_id:     parseInt(newDest),
      dest_group_name:   destGroup?.name ?? null,
      direction: newDir,
      action:    newAction,
      enabled:   true,
      position:  9999,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setStagedPolicies((prev) => [...prev, staged]);
    setNewSource(""); setNewDest(""); setNewDir("both"); setNewAction("allow");
    setShowForm(false);
  };

  const stageUpdate = (key: string, field: Partial<Pick<StagedPolicy, "action" | "enabled">>) => {
    setStagedPolicies((prev) =>
      prev.map((p) => {
        const match = p._localId === key || String(p.id) === key;
        if (!match) return p;
        return { ...p, ...field, _pending: p._pending === "create" ? "create" : "update" };
      })
    );
  };

  const stageDelete = (key: string) => {
    setStagedPolicies((prev) =>
      prev
        .map((p) => {
          const match = p._localId === key || String(p.id) === key;
          if (!match) return p;
          if (p._pending === "create") return null as unknown as StagedPolicy; // new rule never saved
          return { ...p, _pending: "delete" as PendingOp };
        })
        .filter(Boolean)
    );
  };

  // ── Save / Cancel ───────────────────────────────────────────────────────────
  const isSaving =
    setFirewallMutation.isPending || createMutation.isPending ||
    updateMutation.isPending || deleteMutation.isPending;

  const handleSave = async () => {
    // 1. Firewall toggle
    if (stagedFirewall !== null && stagedFirewall !== firewallStatus?.firewall_enabled) {
      await setFirewallMutation.mutateAsync(stagedFirewall);
    }
    // 2. Deletes
    for (const p of stagedPolicies.filter((x) => x._pending === "delete" && x.id !== -1)) {
      await deleteMutation.mutateAsync(p.id);
    }
    // 3. Creates
    for (const p of stagedPolicies.filter((x) => x._pending === "create")) {
      await createMutation.mutateAsync({
        source_group_id: p.source_group_id,
        dest_group_id:   p.dest_group_id,
        direction:       p.direction,
        action:          p.action,
        enabled:         p.enabled,
      });
    }
    // 4. Updates
    for (const p of stagedPolicies.filter((x) => x._pending === "update")) {
      await updateMutation.mutateAsync({ id: p.id, data: { action: p.action, enabled: p.enabled } });
    }
    // 5. Reorder existing policies (skip unsaved creates that still have id=-1)
    if (positionsChanged) {
      const orderedIds = visiblePolicies.filter((p) => p.id > 0).map((p) => p.id);
      if (orderedIds.length > 0) await policiesApi.reorder(orderedIds);
      setPositionsChanged(false);
    }
    // Refresh
    qc.invalidateQueries({ queryKey: ["policies"] });
    qc.invalidateQueries({ queryKey: ["firewall-status"] });
    qc.invalidateQueries({ queryKey: ["firewall-rules"] });
    setStagedFirewall(null);
  };

  const handleCancel = () => {
    setStagedPolicies((serverPolicies ?? []).map((p) => ({ ...p })));
    setStagedFirewall(null);
    setPositionsChanged(false);
    setShowForm(false);
  };

  const getKey = (p: StagedPolicy) => p._localId ?? String(p.id);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4 pb-24">

      {/* ── Firewall master toggle ──────────────────────────────────────────── */}
      <Card className={firewallOn ? "border-primary/40" : "border-muted"}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {firewallOn
                ? <ShieldCheck className="h-6 w-6 text-primary" />
                : <ShieldOff   className="h-6 w-6 text-muted-foreground" />
              }
              <div>
                <p className="font-semibold text-sm">
                  Firewall&nbsp;
                  <Badge variant={firewallOn ? "default" : "secondary"} className="text-xs ml-1">
                    {firewallOn ? "ACTIVO" : "INACTIVO"}
                  </Badge>
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {firewallOn
                    ? `${visiblePolicies.length} regla${visiblePolicies.length !== 1 ? "s" : ""} activa${visiblePolicies.length !== 1 ? "s" : ""} — el acceso se rige por las políticas definidas`
                    : "Modo permisivo — todo el tráfico está permitido (regla implícita: All → All Allow)"
                  }
                </p>
              </div>
            </div>
            <Switch
              checked={firewallOn}
              onCheckedChange={(v) => setStagedFirewall(v)}
              className="data-[state=checked]:bg-primary"
            />
          </div>
        </CardContent>
      </Card>

      {/* ── Default rule banner (when firewall off) ─────────────────────────── */}
      {!firewallOn && (
        <div className="flex items-center gap-2 rounded-md border border-green-500/30 bg-green-500/5 px-4 py-3 text-sm text-green-700 dark:text-green-400">
          <Check className="h-4 w-4 shrink-0" />
          <span>
            <strong>Regla activa:</strong> All Groups → All Groups — <strong>Allow</strong> (bidireccional)
          </span>
        </div>
      )}

      {/* ── Rules section (only when firewall is on) ────────────────────────── */}
      {firewallOn && (
        <>
          {/* Add rule form */}
          {showForm && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Plus className="h-4 w-4" /> Nueva Regla
                </CardTitle>
                <CardDescription>
                  Los miembros del grupo origen accederán a las redes del grupo destino.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Origen (Grupo)</label>
                    <Select value={newSource} onValueChange={setNewSource}>
                      <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                      <SelectContent>
                        {(groups ?? []).map((g: PeerGroup) => (
                          <SelectItem key={g.id} value={String(g.id)}>
                            {g.name}
                            {g.member_count != null && (
                              <span className="text-muted-foreground ml-1">({g.member_count})</span>
                            )}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Destino (Grupo)</label>
                    <Select value={newDest} onValueChange={setNewDest}>
                      <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                      <SelectContent>
                        {(groups ?? []).map((g: PeerGroup) => (
                          <SelectItem key={g.id} value={String(g.id)}>
                            {g.name}
                            {g.member_count != null && (
                              <span className="text-muted-foreground ml-1">({g.member_count})</span>
                            )}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Dirección</label>
                    <Select value={newDir} onValueChange={(v) => setNewDir(v as typeof newDir)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="both">↔ Ambas</SelectItem>
                        <SelectItem value="outbound">→ Saliente</SelectItem>
                        <SelectItem value="inbound">← Entrante</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Acción</label>
                    <Select value={newAction} onValueChange={(v) => setNewAction(v as typeof newAction)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="allow">Permitir</SelectItem>
                        <SelectItem value="deny">Denegar</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-end gap-2">
                    <Button size="sm" onClick={stageAddRule} disabled={!newSource || !newDest}>
                      Agregar
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setShowForm(false)}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Rules table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <div>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Shield className="h-4 w-4" /> Reglas de Firewall
                </CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Las reglas se evalúan <strong>de arriba hacia abajo</strong> — arrastra{" "}
                  <GripVertical className="h-3 w-3 inline-block" /> para cambiar el orden.
                  Prioridad explícita: deny &gt; allow.
                </CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4 mr-1" /> Nueva Regla
              </Button>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              {visiblePolicies.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-muted-foreground">
                  Sin reglas. Con firewall activo y sin reglas, <strong>todo el tráfico será bloqueado</strong>.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/40">
                      <th className="w-8 px-2 py-2" title="Arrastrar para reordenar" />
                      <th className="text-left px-2 py-2 font-medium w-6 text-muted-foreground">#</th>
                      <th className="text-left px-4 py-2 font-medium w-8">Activa</th>
                      <th className="text-left px-4 py-2 font-medium">Origen</th>
                      <th className="text-left px-4 py-2 font-medium">Dirección</th>
                      <th className="text-left px-4 py-2 font-medium">Destino</th>
                      <th className="text-left px-4 py-2 font-medium">Acción</th>
                      <th className="text-right px-4 py-2 font-medium">Eliminar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visiblePolicies.map((p, idx) => {
                      const key = getKey(p);
                      const isNew = p._pending === "create";
                      const isDragging = dragSrcIdx === idx;
                      const isOver = dragOverIdx === idx && dragSrcIdx !== idx;
                      return (
                        <tr
                          key={key}
                          draggable
                          onDragStart={(e) => handleDragStart(e, idx)}
                          onDragOver={(e) => handleDragOver(e, idx)}
                          onDragLeave={handleDragLeave}
                          onDrop={(e) => handleDrop(e, idx)}
                          onDragEnd={handleDragEnd}
                          className={`border-b last:border-0 transition-colors cursor-default ${
                            isDragging ? "opacity-30" :
                            isOver    ? "border-t-2 border-t-primary bg-primary/5" :
                            !p.enabled ? "opacity-50" : ""
                          } ${isNew ? "bg-primary/5" : "hover:bg-muted/10"}`}
                        >
                          {/* drag handle */}
                          <td className="px-2 py-2">
                            <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab active:cursor-grabbing" />
                          </td>
                          {/* row number */}
                          <td className="px-2 py-2 text-xs text-muted-foreground font-mono">
                            {idx + 1}
                          </td>
                          {/* enabled toggle */}
                          <td className="px-4 py-2">
                            <Switch
                              checked={p.enabled}
                              onCheckedChange={(v) => stageUpdate(key, { enabled: v })}
                              className="data-[state=checked]:bg-primary"
                            />
                          </td>
                          {/* source */}
                          <td className="px-4 py-2">
                            <span className="font-medium">
                              {p.source_group_name ?? `Grupo ${p.source_group_id}`}
                            </span>
                            {isNew && <Badge variant="outline" className="ml-2 text-xs py-0">Nuevo</Badge>}
                          </td>
                          {/* direction */}
                          <td className="px-4 py-2">
                            <Badge variant="outline" className="text-xs flex items-center gap-1 w-fit">
                              {directionIcon(p.direction)}
                              {directionLabel[p.direction]}
                            </Badge>
                          </td>
                          {/* dest */}
                          <td className="px-4 py-2 font-medium">
                            {p.dest_group_name ?? `Grupo ${p.dest_group_id}`}
                          </td>
                          {/* action toggle */}
                          <td className="px-4 py-2">
                            <button
                              onClick={() => stageUpdate(key, { action: p.action === "allow" ? "deny" : "allow" })}
                              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                                p.action === "allow"
                                  ? "bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400"
                                  : "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400"
                              }`}
                            >
                              {p.action === "allow"
                                ? <><Check className="h-3 w-3" /> Permitir</>
                                : <><X     className="h-3 w-3" /> Denegar</>
                              }
                            </button>
                          </td>
                          {/* delete */}
                          <td className="px-4 py-2 text-right">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => stageDelete(key)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* ── Live iptables rules ─────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="h-4 w-4" /> Reglas de Firewall Activas (iptables)
              </CardTitle>
              <CardDescription className="text-xs">
                Vista en tiempo real de la cadena <code className="font-mono">NETLOOM-FWD</code>.
                Las reglas se evalúan <strong>de arriba hacia abajo</strong> — la primera coincidencia (ACCEPT o DROP) gana.
                Un DROP al final de cada equipo bloquea todo lo no permitido explícitamente.
              </CardDescription>
            </div>
            <Button size="sm" variant="ghost" onClick={() => refetchRules()}>
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {/* explanation banner */}
          <div className="mx-4 mb-3 flex items-start gap-2 rounded-md border border-blue-400/30 bg-blue-500/5 px-3 py-2 text-xs text-blue-700 dark:text-blue-400">
            <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>
              Cada equipo recibe reglas <strong>ACCEPT</strong> para las redes que tiene permitidas y luego un{" "}
              <strong>DROP</strong> que bloquea todo lo demás. Si un equipo no puede acceder a algún destino,
              revisa las políticas de su grupo o verifica que ese destino esté en una red configurada.
            </span>
          </div>
          {fwRules.length === 0 ? (
            <p className="px-6 py-6 text-center text-sm text-muted-foreground">
              Sin reglas activas en iptables.
            </p>
          ) : (
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="w-8 px-3 py-2 text-left font-semibold font-sans text-muted-foreground">#</th>
                  <th className="w-6 px-3 py-2" />
                  <th className="text-left px-3 py-2 font-semibold font-sans">Acción</th>
                  <th className="text-left px-3 py-2 font-semibold font-sans">Origen</th>
                  <th className="text-left px-3 py-2 font-semibold font-sans">Destino</th>
                  <th className="text-left px-3 py-2 font-semibold font-sans">Detalles</th>
                </tr>
              </thead>
              <tbody>
                {fwRules.map((rule, i) => {
                  const isAccept = rule.target === "ACCEPT";
                  const isDrop   = rule.target === "DROP" || rule.target === "REJECT";
                  return (
                    <tr
                      key={i}
                      className={`border-b last:border-0 ${
                        isAccept ? "bg-green-500/5 border-l-2 border-l-green-500"
                        : isDrop ? "bg-red-500/5 border-l-2 border-l-red-500"
                        : ""
                      }`}
                    >
                      <td className="px-3 py-1.5 text-muted-foreground font-sans">{i + 1}</td>
                      <td className="px-3 py-1.5">
                        {isAccept ? <Check className="h-3 w-3 text-green-500" />
                          : isDrop ? <X className="h-3 w-3 text-red-500" />
                          : null}
                      </td>
                      <td className="px-3 py-1.5">
                        <Badge
                          variant="outline"
                          className={`text-xs py-0 font-mono ${
                            isAccept ? "border-green-400 text-green-600 dark:text-green-400 bg-green-500/10"
                            : isDrop ? "border-red-400 text-red-600 dark:text-red-400 bg-red-500/10"
                            : ""
                          }`}
                        >
                          {rule.target}
                        </Badge>
                      </td>
                      <td className="px-3 py-1.5 text-foreground">{rule.src}</td>
                      <td className="px-3 py-1.5 text-foreground">{rule.dst}</td>
                      <td className="px-3 py-1.5 text-muted-foreground">{rule.extra || "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* ── Save / Cancel bar (sticky bottom) ──────────────────────────────── */}
      {hasPendingChanges && (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between gap-3 border-t bg-background/95 backdrop-blur px-6 py-3 shadow-lg">
          <span className="text-sm text-muted-foreground">
            Hay cambios sin guardar —&nbsp;
            {stagedPolicies.filter((p) => p._pending === "create").length > 0 &&
              `${stagedPolicies.filter((p) => p._pending === "create").length} nueva(s), `}
            {stagedPolicies.filter((p) => p._pending === "update").length > 0 &&
              `${stagedPolicies.filter((p) => p._pending === "update").length} modificada(s), `}
            {stagedPolicies.filter((p) => p._pending === "delete").length > 0 &&
              `${stagedPolicies.filter((p) => p._pending === "delete").length} eliminada(s) `}
            {stagedFirewall !== null && stagedFirewall !== firewallStatus?.firewall_enabled &&
              `+ firewall ${stagedFirewall ? "activado" : "desactivado"}`}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleCancel} disabled={isSaving}>
              <RotateCcw className="h-4 w-4 mr-1" /> Cancelar
            </Button>
            <Button size="sm" onClick={handleSave} disabled={isSaving}>
              <Save className="h-4 w-4 mr-1" />
              {isSaving ? "Guardando..." : "Guardar"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
