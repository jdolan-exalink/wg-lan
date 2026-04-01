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
import { Plus, Trash2, Globe, Building2, ChevronDown, ChevronRight, Router, Server, Laptop, Smartphone, Shield, X } from "lucide-react";
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
};

function NetworkRow({ network }: { network: Network }) {
  const [expanded, setExpanded] = useState(false);
  const [editPeers, setEditPeers] = useState(false);
  const [selectedPeerIds, setSelectedPeerIds] = useState<number[]>(network.peers.map((p: any) => p.id));
  const qc = useQueryClient();

  const del = useMutation({
    mutationFn: (id: number) => networksApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  const assignPeers = useMutation({
    mutationFn: ({ networkId, peerIds }: { networkId: number; peerIds: number[] }) =>
      networksApi.assignPeers(networkId, peerIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["networks"] });
      setEditPeers(false);
    },
  });

  const removePeer = useMutation({
    mutationFn: ({ networkId, peerId }: { networkId: number; peerId: number }) =>
      networksApi.removePeer(networkId, peerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  const { data: allPeers = [] } = useQuery({
    queryKey: ["peers"],
    queryFn: () => peersApi.list().then((r) => r.data),
  });

  return (
    <>
      <tr className="border-b last:border-0 hover:bg-muted/20">
        <td className="px-4 py-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 font-medium"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            {network.name}
          </button>
        </td>
        <td className="px-4 py-2 font-mono text-xs">{network.subnet}</td>
        <td className="px-4 py-2">
          <Badge variant={network.network_type === "lan" ? "default" : "secondary"}>
            {network.network_type === "lan" ? (
              <span className="flex items-center gap-1"><Building2 className="h-3 w-3" />LAN</span>
            ) : (
              <span className="flex items-center gap-1"><Globe className="h-3 w-3" />VPN</span>
            )}
          </Badge>
        </td>
        <td className="px-4 py-2 text-muted-foreground">{network.description ?? "—"}</td>
        <td className="px-4 py-2">
          {network.peer_count > 0 ? (
            <Badge variant="outline">{network.peer_count} peer{network.peer_count !== 1 ? "s" : ""}</Badge>
          ) : (
            <span className="text-muted-foreground/50">—</span>
          )}
        </td>
        <td className="px-4 py-2 text-right">
          <div className="flex items-center justify-end gap-1">
            <Button variant="ghost" size="icon" onClick={() => {
              setSelectedPeerIds(network.peers.map((p: any) => p.id));
              setEditPeers(true);
            }} title="Edit peers">
              <Shield className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => del.mutate(network.id)}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-muted/10">
          <td colSpan={6} className="px-4 py-2">
            <div className="ml-6 space-y-1">
              <p className="text-xs text-muted-foreground font-medium mb-2">Peers asociados a esta red:</p>
              {network.peers.length === 0 ? (
                <p className="text-xs text-muted-foreground">No peers assigned</p>
              ) : (
                network.peers.map((peer: any) => (
                  <div key={peer.id} className="flex items-center gap-3 text-xs py-1">
                    <span className="text-muted-foreground">
                      {peerTypeIcons[peer.device_type ?? peer.peer_type] ?? <Laptop className="h-3 w-3" />}
                    </span>
                    <span className="font-medium">{peer.name}</span>
                    <Badge variant="outline" className="text-[10px]">{peer.peer_type}</Badge>
                    <span className="font-mono text-muted-foreground">{peer.assigned_ip}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-auto"
                      onClick={() => removePeer.mutate({ networkId: network.id, peerId: peer.id })}
                    >
                      <X className="h-3 w-3 text-destructive" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </td>
        </tr>
      )}

      {/* Edit Peers Dialog */}
      <Dialog open={editPeers} onOpenChange={(open) => !open && setEditPeers(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Peers — {network.name}</DialogTitle>
            <DialogDescription>
              Select which peers should have access to this network.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            {allPeers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No peers available.</p>
            ) : (
              allPeers.map((p: Peer) => {
                const checked = selectedPeerIds.includes(p.id);
                return (
                  <label key={p.id} className="flex items-center gap-3 p-2 rounded hover:bg-accent cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedPeerIds((prev) => [...prev, p.id]);
                        } else {
                          setSelectedPeerIds((prev) => prev.filter((id) => id !== p.id));
                        }
                      }}
                      className="h-4 w-4 rounded border-input"
                    />
                    <div className="flex items-center gap-2">
                      {peerTypeIcons[p.device_type ?? p.peer_type]}
                      <span className="text-sm font-medium">{p.name}</span>
                      <Badge variant="outline" className="text-[10px]">{p.peer_type}</Badge>
                      <span className="text-xs font-mono text-muted-foreground">{p.assigned_ip}</span>
                    </div>
                  </label>
                );
              })
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditPeers(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => assignPeers.mutate({ networkId: network.id, peerIds: selectedPeerIds })}
              disabled={assignPeers.isPending}
            >
              {assignPeers.isPending ? "Saving..." : "Save Peers"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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

  const create = useMutation({
    mutationFn: (data: FormData) => networksApi.create(data as Omit<Network, "id">),
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

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">LAN networks de branch offices/servidores y subredes VPN</p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Network
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">New Network</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Name</Label>
                <Input placeholder="Planta Principal" {...register("name")} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1">
                <Label>Subnet (CIDR)</Label>
                <Input placeholder="192.168.1.0/24" {...register("subnet")} />
                {errors.subnet && <p className="text-xs text-destructive">{errors.subnet.message}</p>}
              </div>
              <div className="space-y-1">
                <Label>Type</Label>
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
                <Label>Description</Label>
                <Input placeholder="Optional" {...register("description")} />
              </div>
              <div className="col-span-2 flex gap-2">
                <Button type="submit" size="sm" disabled={isSubmitting}>Save</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2 font-medium">Name</th>
                <th className="text-left px-4 py-2 font-medium">Subnet</th>
                <th className="text-left px-4 py-2 font-medium">Type</th>
                <th className="text-left px-4 py-2 font-medium">Description</th>
                <th className="text-left px-4 py-2 font-medium">Peers</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {networks.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No networks yet</td></tr>
              ) : networks.map((n) => (
                <NetworkRow key={n.id} network={n} />
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
