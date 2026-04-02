import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { groupsApi, networksApi } from "@/api/networks";
import { peersApi } from "@/api/peers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2, Users, ChevronDown, ChevronRight, Info, ArrowRight, Router, Laptop, Smartphone, Server, X, Check, Loader2, Globe } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { Network } from "@/types/network";

const schema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

const peerTypeIcons: Record<string, React.ReactNode> = {
  roadwarrior: <Laptop className="h-3 w-3" />,
  branch_office: <Router className="h-3 w-3" />,
  laptop: <Laptop className="h-3 w-3" />,
  ios: <Smartphone className="h-3 w-3" />,
  android: <Smartphone className="h-3 w-3" />,
  router: <Router className="h-3 w-3" />,
  server: <Server className="h-3 w-3" />,
};

export function GroupsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [expandedGroupId, setExpandedGroupId] = useState<number | null>(null);
  const [addPeersGroupId, setAddPeersGroupId] = useState<number | null>(null);
  const [selectedPeerIds, setSelectedPeerIds] = useState<Set<number>>(new Set());
  const [deleteGroupId, setDeleteGroupId] = useState<number | null>(null);

  // ── Add-network dialog state ──────────────────────────────────────────────
  const [addNetworkGroupId, setAddNetworkGroupId] = useState<number | null>(null);
  const [netName, setNetName] = useState("");
  const [netSubnet, setNetSubnet] = useState("");
  const [netDesc, setNetDesc] = useState("");
  const [netPeerId, setNetPeerId] = useState("");
  const [netError, setNetError] = useState("");

  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const { data: peers = [] } = useQuery({
    queryKey: ["peers"],
    queryFn: () => peersApi.list().then((r) => r.data),
  });

  const { data: networks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  const { data: existingMembers = [], isFetching: membersFetching } = useQuery({
    queryKey: ["group-members", expandedGroupId],
    queryFn: () => expandedGroupId ? groupsApi.getMembers(expandedGroupId).then((r) => r.data) : [],
    enabled: expandedGroupId !== null,
  });

  const create = useMutation({
    mutationFn: (data: FormData) => groupsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["groups"] }); setShowForm(false); },
  });

  const del = useMutation({
    mutationFn: (id: number) => groupsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["groups"] }),
  });

  const addMember = useMutation({
    mutationFn: ({ groupId, peerIds }: { groupId: number; peerIds: number[] }) =>
      groupsApi.addMembers(groupId, peerIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["groups"] });
      qc.invalidateQueries({ queryKey: ["group-members"] });
      setAddPeersGroupId(null);
      setSelectedPeerIds(new Set());
    },
  });

  const removeMember = useMutation({
    mutationFn: ({ groupId, peerId }: { groupId: number; peerId: number }) =>
      groupsApi.removeMember(groupId, peerId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["groups"] });
      qc.invalidateQueries({ queryKey: ["group-members"] });
    },
  });

  const createNetwork = useMutation({
    mutationFn: (data: { name: string; subnet: string; description?: string; peer_id?: number }) =>
      networksApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["networks"] });
      setAddNetworkGroupId(null);
      setNetName(""); setNetSubnet(""); setNetDesc(""); setNetPeerId(""); setNetError("");
    },
    onError: (err: any) => {
      setNetError(err?.response?.data?.detail ?? "Error al crear la red");
    },
  });

  const handleCreateNetwork = () => {
    setNetError("");
    if (!netName.trim()) { setNetError("El nombre es requerido"); return; }
    if (!/^\d+\.\d+\.\d+\.\d+\/\d+$/.test(netSubnet.trim())) { setNetError("Subred inválida — usá el formato CIDR (ej: 10.1.1.0/24)"); return; }
    createNetwork.mutate({
      name: netName.trim(),
      subnet: netSubnet.trim(),
      description: netDesc.trim() || undefined,
      peer_id: netPeerId && netPeerId !== "__none__" ? parseInt(netPeerId) : undefined,
    });
  };

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const existingMemberIds = new Set(existingMembers.map((m) => m.peer_id));
  const availablePeers = peers.filter((p) => !p.is_system && p.peer_type !== "server" && !existingMemberIds.has(p.id));

  // Networks that belong to any member of the currently expanded group
  const groupNetworks = (expandedGroupId !== null)
    ? networks.filter((n) => n.peer_id !== null && existingMembers.some((m) => m.peer_id === n.peer_id))
    : [];

  const togglePeer = (peerId: number) => {
    setSelectedPeerIds((prev) => {
      const next = new Set(prev);
      if (next.has(peerId)) next.delete(peerId);
      else next.add(peerId);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Explanation Card */}
      <Card className="bg-surface-container-low border-primary/10">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary/10 mt-0.5">
              <Info className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-2">
              <h3 className="font-headline font-bold text-on-surface">Grupos de acceso</h3>
              <p className="text-sm text-muted-foreground">
                Un grupo es un perfil de acceso: agrupa peers que comparten las mismas reglas de red.
                Las políticas se definen entre grupos (origen → destino = permitir/denegar), no entre peers individuales.
              </p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Users className="h-3.5 w-3.5" />
                <span>Grupo</span>
                <ArrowRight className="h-3 w-3" />
                <span>Contiene peers</span>
                <ArrowRight className="h-3 w-3" />
                <span>Políticas definen acceso a redes de otros grupos</span>
              </div>
              <p className="text-xs text-muted-foreground/70">
                Un peer puede pertenecer a múltiples grupos. Si un peer no tiene grupo, tiene acceso a todas las redes.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Group Form */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{groups.length} grupo{groups.length !== 1 ? "s" : ""} configurado{groups.length !== 1 ? "s" : ""}</p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Crear grupo
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Nuevo grupo</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit((d) => create.mutateAsync(d).then(() => reset()))} className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Nombre</Label>
                <Input placeholder="soporte" {...register("name")} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1">
                <Label>Descripción</Label>
                <Input placeholder="Opcional" {...register("description")} />
              </div>
              <div className="col-span-2 flex gap-2">
                <Button type="submit" size="sm" disabled={isSubmitting}>Guardar</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>Cancelar</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Groups List */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2 font-medium w-10"></th>
                <th className="text-left px-4 py-2 font-medium">Nombre</th>
                <th className="text-left px-4 py-2 font-medium">Descripción</th>
                <th className="text-left px-4 py-2 font-medium">Miembros</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {groups.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  <div className="flex flex-col items-center gap-2">
                    <Users className="h-6 w-6 text-muted-foreground/30" />
                    <p>No hay grupos configurados</p>
                    <p className="text-xs text-muted-foreground/50">Creá un grupo para empezar a definir políticas de acceso</p>
                  </div>
                </td></tr>
              ) : groups.map((g) => (
                <GroupRow
                  key={g.id}
                  group={g}
                  expanded={expandedGroupId === g.id}
                  onToggle={() => setExpandedGroupId(expandedGroupId === g.id ? null : g.id)}
                  members={expandedGroupId === g.id ? existingMembers : []}
                  membersLoading={expandedGroupId === g.id && membersFetching}
                  groupNetworks={expandedGroupId === g.id ? groupNetworks : []}
                  onAddPeers={() => { setAddPeersGroupId(g.id); setSelectedPeerIds(new Set()); }}
                  onAddNetwork={() => { setAddNetworkGroupId(g.id); setNetPeerId(""); setNetError(""); }}
                  onRemovePeer={(peerId) => removeMember.mutate({ groupId: g.id, peerId })}
                  onDelete={() => setDeleteGroupId(g.id)}
                />
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Add Network Dialog */}
      <Dialog open={addNetworkGroupId !== null} onOpenChange={(open) => {
        if (!open) { setAddNetworkGroupId(null); setNetName(""); setNetSubnet(""); setNetDesc(""); setNetPeerId(""); setNetError(""); }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar red al grupo</DialogTitle>
            <DialogDescription>
              La red quedará asociada al peer gateway seleccionado y formará parte del alcance de políticas de este grupo.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <Label>Nombre de la red</Label>
              <Input
                placeholder="Ej: Planta Exalink"
                value={netName}
                onChange={(e) => setNetName(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label>Subred (CIDR)</Label>
              <Input
                placeholder="Ej: 10.1.1.0/24"
                value={netSubnet}
                onChange={(e) => setNetSubnet(e.target.value)}
                className="font-mono"
              />
            </div>
            <div className="space-y-1">
              <Label>Peer gateway <span className="text-muted-foreground text-xs">(opcional)</span></Label>
              <Select value={netPeerId} onValueChange={setNetPeerId}>
                <SelectTrigger>
                  <SelectValue placeholder="Ninguno (red global)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Ninguno (red global — aplica a todos los grupos)</SelectItem>
                  {existingMembers.filter((m) => m.peer_type !== "server").map((m) => (
                    <SelectItem key={m.peer_id} value={String(m.peer_id)}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{m.peer_name}</span>
                        <Badge variant="outline" className="text-[10px]">{m.peer_type}</Badge>
                        <span className="text-xs font-mono text-muted-foreground">{m.assigned_ip}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Al asignar un peer gateway, la red pertenece a este grupo. Sin gateway, la red es global.
              </p>
            </div>
            <div className="space-y-1">
              <Label>Descripción <span className="text-muted-foreground text-xs">(opcional)</span></Label>
              <Input
                placeholder="Descripción opcional"
                value={netDesc}
                onChange={(e) => setNetDesc(e.target.value)}
              />
            </div>
            {netError && (
              <p className="text-xs text-destructive">{netError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddNetworkGroupId(null)}>
              Cancelar
            </Button>
            <Button onClick={handleCreateNetwork} disabled={createNetwork.isPending}>
              {createNetwork.isPending ? "Creando..." : "Crear red"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Peers Dialog */}
      <Dialog open={addPeersGroupId !== null} onOpenChange={(open) => { if (!open) { setAddPeersGroupId(null); setSelectedPeerIds(new Set()); } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar peers al grupo</DialogTitle>
            <DialogDescription>Seleccioná uno o más peers para agregar.</DialogDescription>
          </DialogHeader>
          <div className="py-2 space-y-1 max-h-72 overflow-y-auto">
            {availablePeers.length === 0 ? (
              <p className="text-sm text-muted-foreground py-2">No hay peers disponibles para agregar.</p>
            ) : (
              availablePeers.map((p) => {
                const selected = selectedPeerIds.has(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => togglePeer(p.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-left transition-colors ${
                      selected ? "bg-primary/10 border border-primary/30" : "hover:bg-muted/50 border border-transparent"
                    }`}
                  >
                    <div className={`h-4 w-4 rounded border flex items-center justify-center flex-shrink-0 ${selected ? "bg-primary border-primary" : "border-muted-foreground/40"}`}>
                      {selected && <Check className="h-3 w-3 text-primary-foreground" />}
                    </div>
                    <span className="text-muted-foreground">{peerTypeIcons[p.device_type ?? p.peer_type]}</span>
                    <span className="font-medium flex-1">{p.name}</span>
                    <Badge variant="outline" className="text-[10px]">{p.peer_type}</Badge>
                    <span className="text-xs font-mono text-muted-foreground">{p.assigned_ip}</span>
                  </button>
                );
              })
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setAddPeersGroupId(null); setSelectedPeerIds(new Set()); }}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (addPeersGroupId && selectedPeerIds.size > 0) {
                  addMember.mutate({ groupId: addPeersGroupId, peerIds: Array.from(selectedPeerIds) });
                }
              }}
              disabled={selectedPeerIds.size === 0 || addMember.isPending}
            >
              {addMember.isPending ? "Agregando..." : `Agregar${selectedPeerIds.size > 0 ? ` (${selectedPeerIds.size})` : ""}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteGroupId !== null} onOpenChange={(open) => !open && setDeleteGroupId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar grupo</DialogTitle>
            <DialogDescription>
              ¿Estás seguro que querés eliminar este grupo? Se eliminarán también todas sus políticas de acceso. Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteGroupId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteGroupId) {
                  del.mutate(deleteGroupId);
                  setDeleteGroupId(null);
                }
              }}
              disabled={del.isPending}
            >
              {del.isPending ? "Eliminando..." : "Eliminar grupo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function GroupRow({
  group,
  expanded,
  onToggle,
  members,
  membersLoading,
  groupNetworks,
  onAddPeers,
  onAddNetwork,
  onRemovePeer,
  onDelete,
}: {
  group: { id: number; name: string; description: string | null; member_count: number };
  expanded: boolean;
  onToggle: () => void;
  members: Array<{ peer_id: number; peer_name: string; peer_type: string; assigned_ip: string }>;
  membersLoading: boolean;
  groupNetworks: Network[];
  onAddPeers: () => void;
  onAddNetwork: () => void;
  onRemovePeer: (peerId: number) => void;
  onDelete: () => void;
}) {
  return (
    <>
      <tr className="border-b last:border-0 hover:bg-muted/20">
        <td className="px-4 py-3">
          <button onClick={onToggle} className="flex items-center gap-2 font-medium">
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </td>
        <td className="px-4 py-3 font-medium font-mono text-xs">{group.name}</td>
        <td className="px-4 py-3 text-muted-foreground">{group.description ?? "—"}</td>
        <td className="px-4 py-3">
          <Badge variant="secondary">{group.member_count} peer{group.member_count !== 1 ? "s" : ""}</Badge>
        </td>
        <td className="px-4 py-3 text-right">
          <div className="flex items-center justify-end gap-1">
            <Button variant="ghost" size="icon" onClick={onDelete} title="Eliminar grupo">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-muted/10">
          <td colSpan={5} className="px-4 py-3">
            <div className="ml-6 space-y-4">

              {/* ── Members ───────────────────────────────────────────────── */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-foreground">Miembros del grupo</p>
                  <Button size="sm" variant="outline" onClick={onAddPeers}>
                    <Plus className="h-3.5 w-3.5 mr-1" /> Agregar peer
                  </Button>
                </div>
                {membersLoading ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Cargando miembros...</span>
                  </div>
                ) : members.length === 0 ? (
                  <p className="text-xs text-muted-foreground/60 italic">Sin miembros — agregá peers para definir políticas de acceso</p>
                ) : (
                  <div className="space-y-1">
                    {members.map((m) => (
                      <div key={m.peer_id} className="flex items-center gap-3 text-xs py-1 px-2 rounded hover:bg-muted/30">
                        <span className="text-muted-foreground">
                          {peerTypeIcons[m.peer_type] ?? <Laptop className="h-3 w-3" />}
                        </span>
                        <span className="font-medium">{m.peer_name}</span>
                        <Badge variant="outline" className="text-[10px]">{m.peer_type}</Badge>
                        <span className="font-mono text-muted-foreground">{m.assigned_ip}</span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 ml-auto"
                          onClick={() => onRemovePeer(m.peer_id)}
                        >
                          <X className="h-3 w-3 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* ── Networks ──────────────────────────────────────────────── */}
              {!membersLoading && (
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-foreground">Redes del grupo</p>
                      <p className="text-[11px] text-muted-foreground">
                        Las redes de los peers miembros son los destinos que las políticas controlan.
                      </p>
                    </div>
                    <Button size="sm" variant="outline" onClick={onAddNetwork}>
                      <Plus className="h-3.5 w-3.5 mr-1" /> Agregar red
                    </Button>
                  </div>
                  {groupNetworks.length === 0 ? (
                    <p className="text-xs text-muted-foreground/60 italic">
                      Ningún peer miembro tiene redes asignadas — agregá una red para habilitar políticas de destino.
                    </p>
                  ) : (
                    <div className="space-y-1">
                      {groupNetworks.map((net) => {
                        const gatewayMember = members.find((m) => m.peer_id === net.peer_id);
                        return (
                          <div key={net.id} className="flex items-center gap-3 text-xs py-1 px-2 rounded bg-muted/20">
                            <Globe className="h-3 w-3 text-muted-foreground shrink-0" />
                            <span className="font-medium">{net.name}</span>
                            <code className="font-mono text-muted-foreground bg-muted/40 px-1 rounded">{net.subnet}</code>
                            {gatewayMember && (
                              <span className="text-muted-foreground/70 flex items-center gap-1">
                                vía{" "}
                                {peerTypeIcons[gatewayMember.peer_type] ?? <Laptop className="h-3 w-3" />}
                                <span>{gatewayMember.peer_name}</span>
                              </span>
                            )}
                            <Badge variant="outline" className="text-[10px] ml-auto">{net.network_type}</Badge>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

            </div>
          </td>
        </tr>
      )}
    </>
  );
}
