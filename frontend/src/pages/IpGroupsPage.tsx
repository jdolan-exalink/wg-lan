import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ipGroupsApi } from "@/api/ip-groups";
import { networksApi } from "@/api/networks";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  Trash2,
  Edit,
  Server,
  MapPin,
  X,
} from "lucide-react";
import type { IpGroup, IpGroupEntry } from "@/types/ip-group";
import type { Network } from "@/types/network";

export function IpGroupsPage() {
  const qc = useQueryClient();

  const { data: ipGroups = [], isLoading } = useQuery({
    queryKey: ["ip-groups"],
    queryFn: () => ipGroupsApi.list().then((r) => r.data),
  });

  const { data: networks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  // ── Dialogs ──
  const [showCreate, setShowCreate] = useState(false);
  const [viewingGroup, setViewingGroup] = useState<IpGroup | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<IpGroup | null>(null);

  // ── Create form ──
  const [newName, setNewName] = useState("");
  const [newNetworkId, setNewNetworkId] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newEntries, setNewEntries] = useState<Array<{ ip_address: string; label?: string }>>([]);
  const [newIpInput, setNewIpInput] = useState("");
  const [newLabelInput, setNewLabelInput] = useState("");

  // ── Add entry form (for viewing group) ──
  const [entryIp, setEntryIp] = useState("");
  const [entryLabel, setEntryLabel] = useState("");

  // ── Mutations ──
  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof ipGroupsApi.create>[0]) => ipGroupsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ip-groups"] });
      resetCreateForm();
      setShowCreate(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => ipGroupsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ip-groups"] });
      setDeleteConfirm(null);
    },
  });

  const addEntryMutation = useMutation({
    mutationFn: ({ groupId, entry }: { groupId: number; entry: { ip_address: string; label?: string } }) =>
      ipGroupsApi.addEntry(groupId, entry),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ip-groups"] });
      setEntryIp("");
      setEntryLabel("");
    },
  });

  const deleteEntryMutation = useMutation({
    mutationFn: ({ groupId, entryId }: { groupId: number; entryId: number }) =>
      ipGroupsApi.deleteEntry(groupId, entryId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ip-groups"] }),
  });

  const resetCreateForm = () => {
    setNewName("");
    setNewNetworkId("");
    setNewDescription("");
    setNewEntries([]);
    setNewIpInput("");
    setNewLabelInput("");
  };

  const handleAddEntryToForm = () => {
    if (!newIpInput.trim()) return;
    setNewEntries((prev) => [...prev, { ip_address: newIpInput.trim(), label: newLabelInput.trim() || undefined }]);
    setNewIpInput("");
    setNewLabelInput("");
  };

  const handleRemoveEntryFromForm = (idx: number) => {
    setNewEntries((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleCreate = () => {
    if (!newName || !newNetworkId) return;
    createMutation.mutate({
      name: newName,
      network_id: parseInt(newNetworkId),
      description: newDescription || undefined,
      entries: newEntries,
    });
  };

  const handleAddEntry = () => {
    if (!viewingGroup || !entryIp.trim()) return;
    addEntryMutation.mutate({
      groupId: viewingGroup.id,
      entry: { ip_address: entryIp.trim(), label: entryLabel.trim() || undefined },
    });
  };

  return (
    <div className="space-y-4">
      {/* ── Explanation ── */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <MapPin className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-sm">Grupos de IPs</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Agrupá IPs específicas dentro de una red para definir políticas granulares.
                Ejemplo: "Servidores" con db=192.168.70.4, ts=192.168.70.5.
                Luego usá estos grupos como destino en las políticas.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Create form ── */}
      {showCreate && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Plus className="h-4 w-4" /> Nuevo Grupo de IPs
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Nombre</Label>
                <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Ej: Servidores" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Red</Label>
                <Select value={newNetworkId} onValueChange={setNewNetworkId}>
                  <SelectTrigger><SelectValue placeholder="Seleccionar red" /></SelectTrigger>
                  <SelectContent>
                    {networks.map((n: Network) => (
                      <SelectItem key={n.id} value={String(n.id)}>
                        {n.name} ({n.subnet})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Descripción</Label>
              <Input value={newDescription} onChange={(e) => setNewDescription(e.target.value)} placeholder="Opcional" />
            </div>

            {/* Entries */}
            <div className="space-y-2">
              <Label className="text-xs">IPs del grupo</Label>
              <div className="flex gap-2">
                <Input
                  className="flex-1"
                  value={newIpInput}
                  onChange={(e) => setNewIpInput(e.target.value)}
                  placeholder="192.168.70.4"
                  onKeyDown={(e) => e.key === "Enter" && handleAddEntryToForm()}
                />
                <Input
                  className="w-32"
                  value={newLabelInput}
                  onChange={(e) => setNewLabelInput(e.target.value)}
                  placeholder="label (ej: db)"
                  onKeyDown={(e) => e.key === "Enter" && handleAddEntryToForm()}
                />
                <Button size="sm" onClick={handleAddEntryToForm} disabled={!newIpInput.trim()}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {newEntries.length > 0 && (
                <div className="space-y-1 mt-2">
                  {newEntries.map((e, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm bg-muted/30 rounded-md px-3 py-1.5">
                      <Server className="h-3 w-3 text-muted-foreground" />
                      <code className="font-mono text-xs">{e.ip_address}</code>
                      {e.label && <Badge variant="outline" className="text-xs py-0">{e.label}</Badge>}
                      <button onClick={() => handleRemoveEntryFromForm(i)} className="ml-auto text-muted-foreground hover:text-destructive">
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={() => { setShowCreate(false); resetCreateForm(); }}>
                Cancelar
              </Button>
              <Button size="sm" onClick={handleCreate} disabled={createMutation.isPending || !newName || !newNetworkId}>
                Crear
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── IP Groups list ── */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between py-3">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <MapPin className="h-4 w-4" /> Grupos de IPs
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              {ipGroups.length} grupo{ipGroups.length !== 1 ? "s" : ""} definido{ipGroups.length !== 1 ? "s" : ""}
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" /> Nuevo Grupo
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">Cargando...</p>
          ) : ipGroups.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              Sin grupos de IPs. Creá uno para empezar.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Nombre</th>
                  <th className="text-left px-4 py-2 font-medium">Red</th>
                  <th className="text-left px-4 py-2 font-medium">IPs</th>
                  <th className="text-left px-4 py-2 font-medium">Descripción</th>
                  <th className="text-right px-4 py-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {ipGroups.map((g: IpGroup) => (
                  <tr key={g.id} className="border-b last:border-0 hover:bg-muted/10 transition-colors">
                    <td className="px-4 py-2 font-medium">
                      <button
                        className="text-left hover:text-primary transition-colors"
                        onClick={() => setViewingGroup(g)}
                      >
                        {g.name}
                      </button>
                    </td>
                    <td className="px-4 py-2">
                      <span className="text-muted-foreground text-xs">{g.network_name}</span>
                      <code className="text-xs ml-1 font-mono">{g.subnet}</code>
                    </td>
                    <td className="px-4 py-2">
                      <Badge variant="secondary" className="text-xs">{g.entry_count}</Badge>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-[200px] truncate">
                      {g.description || "—"}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setViewingGroup(g)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteConfirm(g)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* ── View group detail dialog ── */}
      <Dialog open={!!viewingGroup} onOpenChange={(open) => !open && setViewingGroup(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              {viewingGroup?.name}
            </DialogTitle>
            <DialogDescription>
              {viewingGroup?.network_name} ({viewingGroup?.subnet})
              {viewingGroup?.description && ` — ${viewingGroup.description}`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                className="flex-1"
                value={entryIp}
                onChange={(e) => setEntryIp(e.target.value)}
                placeholder="192.168.70.4"
                onKeyDown={(e) => e.key === "Enter" && handleAddEntry()}
              />
              <Input
                className="w-28"
                value={entryLabel}
                onChange={(e) => setEntryLabel(e.target.value)}
                placeholder="label"
                onKeyDown={(e) => e.key === "Enter" && handleAddEntry()}
              />
              <Button size="sm" onClick={handleAddEntry} disabled={!entryIp.trim() || addEntryMutation.isPending}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {viewingGroup?.entries.length === 0 && !addEntryMutation.isPending && (
              <p className="text-xs text-muted-foreground text-center py-4">Sin IPs definidas</p>
            )}

            {viewingGroup?.entries.map((e: IpGroupEntry) => (
              <div key={e.id} className="flex items-center gap-2 text-sm bg-muted/30 rounded-md px-3 py-1.5">
                <Server className="h-3 w-3 text-muted-foreground shrink-0" />
                <code className="font-mono text-xs">{e.ip_address}</code>
                {e.label && <Badge variant="outline" className="text-xs py-0">{e.label}</Badge>}
                <button
                  onClick={() => deleteEntryMutation.mutate({ groupId: viewingGroup.id, entryId: e.id })}
                  className="ml-auto text-muted-foreground hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Delete confirmation ── */}
      <Dialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar Grupo de IPs</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de eliminar "{deleteConfirm?.name}"? Esta acción no se puede deshacer.
              Si hay políticas que usan este grupo, deberás eliminarlas primero.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancelar</Button>
            <Button variant="destructive" onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}>
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
