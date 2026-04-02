import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { networksApi, peersApi } from "@/api/networks";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Trash2, Globe, Building2, ChevronDown, ChevronRight, Router, Server, Laptop, Smartphone, User, X, ArrowRight, Info, CheckCircle2 } from "lucide-react";
import type { Network } from "@/types/network";
import type { Peer } from "@/types/peer";

const schema = z.object({
  name: z.string().min(1, "Required"),
  subnet: z.string().regex(/^\d+\.\d+\.\d+\.\d+\/\d+$/, "Invalid CIDR"),
  description: z.string().optional(),
  network_type: z.enum(["lan", "vpn"]).default("lan"),
  is_default: z.boolean().default(false),
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
  user: <User className="h-3 w-3" />,
};

function GatewayBadge({ peerId, allPeers }: { peerId: number | null; allPeers: Peer[] }) {
  if (!peerId) return <span className="text-xs text-muted-foreground/50">Sin gateway</span>;
  const peer = allPeers.find((p) => p.id === peerId);
  if (!peer) return <span className="text-xs text-muted-foreground/50">Desconocido</span>;
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{peerTypeIcons[peer.device_type ?? peer.peer_type]}</span>
      <span className="text-xs font-medium">{peer.name}</span>
      <span className="text-[10px] font-mono text-muted-foreground">{peer.assigned_ip}</span>
    </div>
  );
}

function AddPeerToNetwork({ networkId, allPeers, assignedPeerIds }: { networkId: number; allPeers: Peer[]; assignedPeerIds: number[] }) {
  const [open, setOpen] = useState(false);
  const [selectedPeerId, setSelectedPeerId] = useState<number | null>(null);
  const qc = useQueryClient();

  const addPeer = useMutation({
    mutationFn: ({ networkId, peerId }: { networkId: number; peerId: number }) =>
      networksApi.addPeer(networkId, peerId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["networks"] });
      setOpen(false);
      setSelectedPeerId(null);
    },
  });

  const available = allPeers.filter((p) => !assignedPeerIds.includes(p.id));

  if (available.length === 0) return null;

  return (
    <>
      <Button variant="ghost" size="icon" onClick={() => setOpen(true)} title="Agregar peer a esta red">
        <Plus className="h-4 w-4" />
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar peer a la red</DialogTitle>
            <DialogDescription>Seleccioná el peer que querés agregar.</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-2">
            <Select
              value={selectedPeerId?.toString() ?? ""}
              onValueChange={(v) => setSelectedPeerId(parseInt(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Elegir peer..." />
              </SelectTrigger>
              <SelectContent>
                {available.map((p) => (
                  <SelectItem key={p.id} value={p.id.toString()}>
                    <div className="flex items-center gap-2">
                      {peerTypeIcons[p.device_type ?? p.peer_type]}
                      <span>{p.name}</span>
                      {p.is_system && (
                        <Badge variant="secondary" className="text-[10px]">Server</Badge>
                      )}
                      {!p.is_system && (
                        <Badge variant="outline" className="text-[10px]">{p.peer_type}</Badge>
                      )}
                      <span className="text-xs font-mono text-muted-foreground">{p.assigned_ip}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setOpen(false); setSelectedPeerId(null); }}>
              Cancel
            </Button>
            <Button
              onClick={() => selectedPeerId && addPeer.mutate({ networkId, peerId: selectedPeerId })}
              disabled={!selectedPeerId || addPeer.isPending}
            >
              {addPeer.isPending ? "Agregando..." : "Agregar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function NetworkRow({ network, allPeers }: { network: Network; allPeers: Peer[] }) {
  const [expanded, setExpanded] = useState(false);
  const qc = useQueryClient();

  const del = useMutation({
    mutationFn: (id: number) => networksApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  const removePeer = useMutation({
    mutationFn: ({ networkId, peerId }: { networkId: number; peerId: number }) =>
      networksApi.removePeer(networkId, peerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  const assignedPeerIds = network.peers.map((p: any) => p.id);

  return (
    <>
      <tr className="border-b last:border-0 hover:bg-muted/20">
        <td className="px-4 py-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 font-medium"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            {network.name}
          </button>
        </td>
        <td className="px-4 py-3 font-mono text-xs">{network.subnet}</td>
        <td className="px-4 py-3">
          <Badge variant={network.network_type === "lan" ? "default" : "secondary"}>
            {network.network_type === "lan" ? (
              <span className="flex items-center gap-1"><Building2 className="h-3 w-3" />LAN</span>
            ) : (
              <span className="flex items-center gap-1"><Globe className="h-3 w-3" />VPN</span>
            )}
          </Badge>
        </td>
        <td className="px-4 py-3">
          <GatewayBadge peerId={network.peer_id} allPeers={allPeers} />
        </td>
        <td className="px-4 py-3">
          {network.peer_count > 0 ? (
            <Badge variant="outline">{network.peer_count} peer{network.peer_count !== 1 ? "s" : ""}</Badge>
          ) : (
            <span className="text-muted-foreground/50">—</span>
          )}
        </td>
        <td className="px-4 py-3 text-right">
          <div className="flex items-center justify-end gap-1">
            <AddPeerToNetwork networkId={network.id} allPeers={allPeers} assignedPeerIds={assignedPeerIds} />
            <Button variant="ghost" size="icon" onClick={() => del.mutate(network.id)}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-muted/10">
          <td colSpan={6} className="px-4 py-3">
            <div className="ml-6 space-y-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Router className="h-3.5 w-3.5" />
                <span>Gateway:</span>
                <GatewayBadge peerId={network.peer_id} allPeers={allPeers} />
                <ArrowRight className="h-3 w-3 mx-1" />
                <span>Red:</span>
                <span className="font-mono text-primary">{network.subnet}</span>
              </div>
              <div className="border-t border-muted-foreground/10 pt-2">
                <p className="text-xs text-muted-foreground font-medium mb-2">Peers con acceso:</p>
                {network.peers.length === 0 ? (
                  <p className="text-xs text-muted-foreground/50">Ningún peer tiene acceso asignado</p>
                ) : (
                  <div className="space-y-1">
                    {network.peers.map((peer: any) => (
                      <div key={peer.id} className="flex items-center gap-3 text-xs py-1 px-2 rounded hover:bg-muted/30">
                        <span className="text-muted-foreground">
                          {peerTypeIcons[peer.device_type ?? peer.peer_type] ?? <Laptop className="h-3 w-3" />}
                        </span>
                        <span className="font-medium">{peer.name}</span>
                        {peer.is_system ? (
                          <Badge variant="secondary" className="text-[10px]">Server</Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px]">{peer.peer_type}</Badge>
                        )}
                        <span className="font-mono text-muted-foreground">{peer.assigned_ip}</span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 ml-auto"
                          onClick={() => removePeer.mutate({ networkId: network.id, peerId: peer.id })}
                        >
                          <X className="h-3 w-3 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export function NetworksPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: networks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  const { data: allPeers = [] } = useQuery({
    queryKey: ["peers"],
    queryFn: () => peersApi.list().then((r) => r.data),
  });

  const create = useMutation({
    mutationFn: (data: FormData) => networksApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["networks"] }); setShowForm(false); },
  });

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset, setValue, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { network_type: "lan" },
  });

  const onSubmit = async (data: FormData) => {
    await create.mutateAsync(data);
    reset();
  };

  const bovpnPeers = allPeers.filter((p: Peer) => p.peer_type === "branch_office");
  const lanNetworks = networks.filter((n) => n.network_type === "lan");
  const vpnNetworks = networks.filter((n) => n.network_type === "vpn");

  const applyChanges = useMutation({
    mutationFn: () => networksApi.apply(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["networks"] });
      qc.invalidateQueries({ queryKey: ["peers"] });
    },
  });

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
              <h3 className="font-headline font-bold text-on-surface">Redes y acceso entre peers</h3>
              <p className="text-sm text-muted-foreground">
                Acá se gestionan las redes que los peers BOVPN exponen al resto de la VPN.
                Cuando creás un Branch Office, las subredes remotas se registran automáticamente como redes con ese peer como <strong>gateway</strong>.
              </p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Router className="h-3.5 w-3.5" />
                <span>Gateway BOVPN</span>
                <ArrowRight className="h-3 w-3" />
                <span>Expone su red local</span>
                <ArrowRight className="h-3 w-3" />
                <span>Otros peers acceden según las políticas</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* BOVPN Peers Summary */}
      {bovpnPeers.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-medium font-headline text-on-surface">Branch Offices activos</CardTitle>
                <CardDescription>Peers BOVPN y las redes que exponen</CardDescription>
              </div>
              <Button
                size="sm"
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={() => applyChanges.mutate()}
                disabled={applyChanges.isPending}
              >
                {applyChanges.isPending ? (
                  <span className="flex items-center gap-2">Aplicando...</span>
                ) : (
                  <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4" /> Aplicar cambios</span>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4">
              {bovpnPeers.map((peer: Peer) => (
                <div key={peer.id} className="bg-surface-container rounded-lg p-4 border border-outline-variant/10">
                  <div className="flex items-center gap-2">
                    <Router className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold text-on-surface">{peer.name}</span>
                    <Badge variant="outline" className="text-[10px]">{peer.assigned_ip}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* LAN Networks Table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-medium font-headline text-on-surface">Redes LAN</CardTitle>
              <CardDescription>Subredes expuestas por branch offices</CardDescription>
            </div>
            <Button size="sm" onClick={() => setShowForm(!showForm)}>
              <Plus className="h-4 w-4" /> Agregar red
            </Button>
          </div>
        </CardHeader>

        {showForm && (
          <CardContent className="pb-4">
            <Card className="bg-muted/30">
              <CardHeader><CardTitle className="text-sm">Nueva red</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label>Nombre</Label>
                    <Input placeholder="Planta Principal" {...register("name")} />
                    {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                  </div>
                  <div className="space-y-1">
                    <Label>Subnet (CIDR)</Label>
                    <Input placeholder="192.168.1.0/24" {...register("subnet")} />
                    {errors.subnet && <p className="text-xs text-destructive">{errors.subnet.message}</p>}
                  </div>
                  <div className="space-y-1">
                    <Label>Tipo</Label>
                    <Select
                      value={watch("network_type")}
                      onValueChange={(v) => setValue("network_type", v as "lan" | "vpn")}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="lan">
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4" />
                            LAN
                          </div>
                        </SelectItem>
                        <SelectItem value="vpn">
                          <div className="flex items-center gap-2">
                            <Globe className="h-4 w-4" />
                            VPN
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
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
          </CardContent>
        )}

        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2 font-medium">Red</th>
                <th className="text-left px-4 py-2 font-medium">Subnet</th>
                <th className="text-left px-4 py-2 font-medium">Tipo</th>
                <th className="text-left px-4 py-2 font-medium">Gateway (BOVPN)</th>
                <th className="text-left px-4 py-2 font-medium">Acceso</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {lanNetworks.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  <div className="flex flex-col items-center gap-2">
                    <Building2 className="h-6 w-6 text-muted-foreground/30" />
                    <p>No hay redes LAN registradas</p>
                    <p className="text-xs text-muted-foreground/50">Creá un Branch Office con subredes remotas para agregar redes automáticamente</p>
                  </div>
                </td></tr>
              ) : lanNetworks.map((n) => (
                <NetworkRow key={n.id} network={n} allPeers={allPeers} />
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* VPN Networks Table */}
      {vpnNetworks.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium font-headline text-on-surface">Redes VPN</CardTitle>
            <CardDescription>Subredes de túneles VPN site-to-site</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Red</th>
                  <th className="text-left px-4 py-2 font-medium">Subnet</th>
                  <th className="text-left px-4 py-2 font-medium">Tipo</th>
                  <th className="text-left px-4 py-2 font-medium">Gateway</th>
                  <th className="text-left px-4 py-2 font-medium">Acceso</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {vpnNetworks.map((n) => (
                  <NetworkRow key={n.id} network={n} allPeers={allPeers} />
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
