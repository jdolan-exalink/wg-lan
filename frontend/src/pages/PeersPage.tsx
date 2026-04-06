import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { peersApi } from "@/api/peers";
import { networksApi, groupsApi } from "@/api/networks";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { formatHandshake, formatBytes } from "@/lib/utils";
import {
  Plus, Download, QrCode, RotateCcw, Trash2,
  Laptop, Smartphone, Router, Server, ChevronLeft, ChevronRight,
  Building2, User, Monitor, Apple,
} from "lucide-react";
import type { Peer } from "@/types/peer";

type PeerConfigFormat = "standard" | "mikrotik";

async function downloadPeerConfigFile(peer: Peer, format: PeerConfigFormat): Promise<void> {
  const url = format === "mikrotik"
    ? peersApi.mikrotikConfigUrl(peer.id)
    : peersApi.configUrl(peer.id);
  const filename = format === "mikrotik"
    ? `${peer.name}-mikrotik.txt`
    : `${peer.name}.conf`;

  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

function PeerStatusDot({ peer }: { peer: Peer }) {
  if (peer.is_system) {
    return (
      <div className="flex items-center justify-center">
        <span
          className="h-3 w-3 rounded-full bg-green-500 inline-block"
          title="Servidor WireGuard online"
          style={{ animation: "statusPulse 2s ease-in-out infinite" }}
        />
      </div>
    );
  }

  const isOnline = peer.is_online;
  const syncStatus = peer.sync_status;

  if (isOnline && syncStatus === "yellow") {
    return (
      <div className="flex items-center justify-center">
        <span
          className="h-3 w-3 rounded-full inline-block"
          title="Conectado con versión anterior"
          style={{ animation: "trafficLight 6s ease-in-out infinite" }}
        />
      </div>
    );
  }

  const color = isOnline ? "bg-green-500" : "bg-red-500";
  const title = isOnline ? "Conectado" : "Desconectado";

  return (
    <div className="flex items-center justify-center">
      <span
        className={`h-3 w-3 rounded-full ${color} inline-block`}
        title={title}
        style={{ animation: "statusPulse 2s ease-in-out infinite" }}
      />
    </div>
  );
}

function QrCodeDialog({ peer, open, onOpenChange }: { peer: Peer | null; open: boolean; onOpenChange: (open: boolean) => void }) {
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!peer || !open) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setQrSrc(null);

    fetch(`/api/peers/${peer.id}/qrcode`, { credentials: "include" })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `HTTP ${res.status}`);
        }
        return res.blob();
      })
      .then((blob) => {
        if (!cancelled) {
          setQrSrc(URL.createObjectURL(blob));
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [peer?.id, open]);

  if (!peer) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>QR Code — {peer.name}</DialogTitle>
          <DialogDescription>Scan with the WireGuard app to configure this peer.</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col items-center gap-4 py-4">
          {loading && <p className="text-sm text-muted-foreground">Loading QR code...</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {qrSrc && <img src={qrSrc} alt="QR code" className="max-w-xs border rounded" />}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void downloadPeerConfigFile(peer, "standard")}
            >
              <Download className="h-4 w-4 mr-2" /> Standard (.conf)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void downloadPeerConfigFile(peer, "mikrotik")}
            >
              <Download className="h-4 w-4 mr-2" /> MikroTik (.txt)
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

type WizardType = "roadwarrior" | "branch_office" | null;

// ─── Edit Peer Form ─────────────────────────────────────────────────────────

function EditPeerForm({ peer, onSuccess, onCancel }: { peer: Peer; onSuccess: () => void; onCancel: () => void }) {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm({
    defaultValues: {
      name: peer.name,
      description: peer.description || "",
      device_type: peer.device_type || "laptop",
    },
  });

  const onSubmit = async (data: { name: string; description: string; device_type: string }) => {
    await peersApi.update(peer.id, {
      name: data.name,
      description: data.description || null,
      device_type: data.device_type as "laptop" | "ios" | "android" | "server" | "router" | "user",
    });
    onSuccess();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label className="text-xs font-semibold">Name</Label>
        <Input {...register("name")} className="mt-1" />
      </div>
      <div>
        <Label className="text-xs font-semibold">Description</Label>
        <Input {...register("description")} placeholder="Optional description" className="mt-1" />
      </div>
      <div>
        <Label className="text-xs font-semibold">Device Type</Label>
        <select {...register("device_type")} className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm mt-1">
          <option value="laptop">Laptop</option>
          <option value="ios">iOS</option>
          <option value="android">Android</option>
          <option value="server">Server</option>
        </select>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button type="submit" disabled={isSubmitting} size="sm">
          {isSubmitting ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}

const rwSchema = z.object({
  name: z.string().min(1, "Required"),
  device_type: z.enum(["laptop", "ios", "android", "server"]),
  tunnel_mode: z.enum(["full", "split"]),
  network_id: z.coerce.number().optional().nullable(),
  dns: z.string().optional(),
  group_ids: z.array(z.coerce.number()),
  persistent_keepalive: z.coerce.number().default(25),
});

const boSchema = z.object({
  name: z.string().min(1, "Required"),
  device_type: z.enum(["router", "server"]),
  network_id: z.coerce.number().optional().nullable(),
  remote_subnets: z.array(z.object({ cidr: z.string().regex(/^\d+\.\d+\.\d+\.\d+\/\d+$/, "Invalid CIDR") })).min(1),
  dns: z.string().optional(),
  group_ids: z.array(z.coerce.number()),
  persistent_keepalive: z.coerce.number().default(25),
});

type RWForm = z.infer<typeof rwSchema>;
type BOForm = z.infer<typeof boSchema>;

const deviceIcons: Record<string, React.ReactNode> = {
  laptop: <Laptop className="h-4 w-4" />,
  ios: <Smartphone className="h-4 w-4" />,
  android: <Smartphone className="h-4 w-4" />,
  router: <Router className="h-4 w-4" />,
  server: <Server className="h-4 w-4" />,
  user: <User className="h-4 w-4" />,
};

const osIcons: Record<string, React.ReactNode> = {
  windows: (
    <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 5.5l8-1.5v11l-8-1.5V5.5zm8 13l8-1.5v-11l-8 1.5v11zm0-14.5l8 1.5v11l-8-1.5V4zm0 14.5l8-1.5v-11l-8 1.5v11z"/>
    </svg>
  ),
  macos: <Apple className="h-3.5 w-3.5" />,
  linux: (
    <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 4.69 2 8c0 1.65.67 3.14 1.76 4.26l-1.76 5.74L9 16v3c0 1.1.9 2 2 2h4c1.1 0 2-.9 2-2v-3l2.82-1.26L20.24 12c1.09-1.12 1.76-2.61 1.76-4.26 0-3.31-4.48-6-10-6zm2 14h-4v-2h4v2zm-4-4V9l-2 1 2 1v5h4l-2-1z"/>
    </svg>
  ),
  android: (
    <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85c-.29-.15-.65-.06-.83.26l-1.59 2.76l-2.13-2.13c-.18-.18-.43-.28-.7-.28c-.28 0-.53.11-.71.29L8.52 9.68c-.18.18-.28.43-.28.71c0 .27.11.52.28.7l4.11 4.11c.18.18.43.28.7.28c.27 0 .52-.11.7-.28l3.47-6.08zM5.83 12.5c-.48.48-.77 1.12-.77 1.82c0 .7.29 1.34.77 1.82l2.17 2.17c.48.48 1.12.77 1.82.77c.7 0 1.34-.29 1.82-.77l2.17-2.17c.48-.48.77-1.12.77-1.82c0-.7-.29-1.34-.77-1.82l-2.17-2.17c-.48-.48-1.12-.77-1.82-.77c-.7 0-1.34.29-1.82.77L5.83 12.5z"/>
    </svg>
  ),
  ios: <Smartphone className="h-3.5 w-3.5" />,
};

export function PeersPage() {
  const qc = useQueryClient();
  const [wizard, setWizard] = useState<WizardType>(null);
  const [qrPeer, setQrPeer] = useState<Peer | null>(null);
  const [editGroupsPeer, setEditGroupsPeer] = useState<Peer | null>(null);
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);
  const [revokePeer, setRevokePeer] = useState<Peer | null>(null);
  const [editPeer, setEditPeer] = useState<Peer | null>(null);

  const { data: peers = [] } = useQuery({
    queryKey: ["peers"],
    queryFn: () => peersApi.list().then((r) => r.data),
    refetchInterval: 15_000,
  });

  const { data: networks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const networkMap = new Map(networks.map((n) => [n.id, n.name]));

  const updatePeerGroups = useMutation({
    mutationFn: ({ peerId, groupIds }: { peerId: number; groupIds: number[] }) =>
      peersApi.updateGroups(peerId, groupIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["peers"] });
      qc.invalidateQueries({ queryKey: ["groups"] });
      setEditGroupsPeer(null);
    },
  });

  const toggle = useMutation({
    mutationFn: (id: number) => peersApi.toggle(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["peers"] }),
  });

  const revoke = useMutation({
    mutationFn: (id: number) => peersApi.revoke(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["peers"] });
      setRevokePeer(null);
    },
    onError: (error: any) => {
      console.error("Failed to revoke peer:", error);
      alert(error.response?.data?.detail || "Failed to revoke peer");
    },
  });

  const regenKeys = useMutation({
    mutationFn: (id: number) => peersApi.regenerateKeys(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["peers"] }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{peers.length} peer{peers.length !== 1 ? "s" : ""} configured</p>
        <div className="flex gap-2">
          <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white border-0" onClick={() => setWizard("roadwarrior")}>
            <User className="h-4 w-4" /> RoadWarrior
          </Button>
          <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white border-0" onClick={() => setWizard("branch_office")}>
            <Building2 className="h-4 w-4" /> BOVPN
          </Button>
        </div>
      </div>

      {wizard === "roadwarrior" && (
        <RoadWarriorWizard onDone={() => { setWizard(null); qc.invalidateQueries({ queryKey: ["peers"] }); }} onCancel={() => setWizard(null)} />
      )}
      {wizard === "branch_office" && (
        <BranchOfficeWizard onDone={() => { setWizard(null); qc.invalidateQueries({ queryKey: ["peers"] }); }} onCancel={() => setWizard(null)} />
      )}

      {qrPeer && (
        <QrCodeDialog peer={qrPeer} open={!!qrPeer} onOpenChange={(open) => !open && setQrPeer(null)} />
      )}

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2 font-medium w-10"></th>
                <th className="text-left px-4 py-2 font-medium">Name</th>
                <th className="text-left px-4 py-2 font-medium">Type</th>
                <th className="text-left px-4 py-2 font-medium">OS</th>
                <th className="text-left px-4 py-2 font-medium">VPN IP</th>
                <th className="text-left px-4 py-2 font-medium">Shared LAN</th>
                <th className="text-left px-4 py-2 font-medium">Tunnel</th>
                <th className="text-left px-4 py-2 font-medium w-16">Power</th>
                <th className="text-right px-4 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {peers.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">No peers yet — use a wizard above</td></tr>
              ) : [...peers].sort((a, b) => (a.is_system ? -1 : b.is_system ? 1 : 0)).map((p) => (
                <tr key={p.id} className="border-b last:border-0 hover:bg-muted/20">
                  <td className="px-4 py-2">
                    <PeerStatusDot peer={p} />
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      {p.device_type && deviceIcons[p.device_type]}
                      <span className="font-medium">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground capitalize">{p.peer_type.replace("_", " ")}</td>
                  <td className="px-4 py-2">
                    {p.os && osIcons[p.os] ? (
                      <div className="flex items-center gap-1.5" title={p.os}>
                        {osIcons[p.os]}
                      </div>
                    ) : (
                      <span className="text-muted-foreground/50 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{p.assigned_ip.split('/')[0]}</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">
                    {p.peer_type === "branch_office" && p.remote_subnets && p.remote_subnets.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {p.remote_subnets.map((subnet, i) => (
                          <Badge key={i} variant="outline" className="text-[10px] px-1.5 py-0">{subnet}</Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground/50">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant={p.tunnel_mode === "full" ? "default" : "outline"}>{p.tunnel_mode}</Badge>
                  </td>
                  <td className="px-4 py-2">
                    {!p.is_system && (
                      <Switch
                        checked={p.is_enabled}
                        onCheckedChange={() => toggle.mutate(p.id)}
                        className={p.is_enabled ? "data-[state=checked]:bg-green-500" : "data-[state=unchecked]:bg-gray-500"}
                      />
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Edit peer"
                        onClick={() => setEditPeer(p)}
                      >
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Edit groups"
                        onClick={() => {
                          setEditGroupsPeer(p);
                          setSelectedGroupIds(p.group_ids || []);
                        }}
                      >
                        <span className="material-symbols-outlined text-[18px]">group</span>
                      </Button>
                      {!p.is_system && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Download standard config"
                            onClick={() => void downloadPeerConfigFile(p, "standard")}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          {p.peer_type !== "roadwarrior" && (
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Download MikroTik RouterOS commands"
                              onClick={() => void downloadPeerConfigFile(p, "mikrotik")}
                            >
                              <Router className="h-4 w-4" />
                            </Button>
                          )}
                          {p.peer_type !== "branch_office" && (
                            <Button variant="ghost" size="icon" title="Show QR" onClick={() => setQrPeer(p)}>
                              <QrCode className="h-4 w-4" />
                            </Button>
                          )}
                          <Button variant="ghost" size="icon" title="Regenerate keys" onClick={() => regenKeys.mutate(p.id)}>
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" title="Delete peer" onClick={() => setRevokePeer(p)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Edit Groups Dialog */}
      <Dialog open={editGroupsPeer !== null} onOpenChange={(open) => !open && setEditGroupsPeer(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Groups — {editGroupsPeer?.name}</DialogTitle>
            <DialogDescription>
              Select the groups this peer should belong to. Changes will take effect after applying config.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            {groups.length === 0 ? (
              <p className="text-sm text-muted-foreground">No groups available. Create groups first.</p>
            ) : (
              groups.map((g) => (
                <label key={g.id} className="flex items-center gap-3 p-2 rounded hover:bg-accent cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedGroupIds.includes(g.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedGroupIds((prev) => [...prev, g.id]);
                      } else {
                        setSelectedGroupIds((prev) => prev.filter((id) => id !== g.id));
                      }
                    }}
                    className="h-4 w-4 rounded border-input"
                  />
                  <div>
                    <span className="text-sm font-medium">{g.name}</span>
                    {g.description && <p className="text-xs text-muted-foreground">{g.description}</p>}
                  </div>
                </label>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditGroupsPeer(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editGroupsPeer) {
                  updatePeerGroups.mutate({ peerId: editGroupsPeer.id, groupIds: selectedGroupIds });
                }
              }}
              disabled={updatePeerGroups.isPending}
            >
              {updatePeerGroups.isPending ? "Saving..." : "Save Groups"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={revokePeer !== null} onOpenChange={(open) => !open && setRevokePeer(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Peer</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{revokePeer?.name}</strong>? This action will disable the peer and remove it from the WireGuard configuration.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRevokePeer(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (revokePeer) {
                  revoke.mutate(revokePeer.id);
                }
              }}
              disabled={revoke.isPending}
            >
              {revoke.isPending ? "Deleting..." : "Delete Peer"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Peer Dialog */}
      <Dialog open={!!editPeer} onOpenChange={(v) => !v && setEditPeer(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Peer</DialogTitle>
          </DialogHeader>
          {editPeer && (
            <EditPeerForm
              peer={editPeer}
              onSuccess={() => {
                qc.invalidateQueries({ queryKey: ["peers"] });
                setEditPeer(null);
              }}
              onCancel={() => setEditPeer(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── RoadWarrior Wizard ─────────────────────────────────────────────────────

function RoadWarriorWizard({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [step, setStep] = useState(0);
  const [createdPeer, setCreatedPeer] = useState<Peer | null>(null);
  const [showQr, setShowQr] = useState(false);

  const { data: networks = [] } = useQuery({ queryKey: ["networks"], queryFn: () => networksApi.list().then((r) => r.data) });
  const { data: groups = [] } = useQuery({ queryKey: ["groups"], queryFn: () => groupsApi.list().then((r) => r.data) });

  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<RWForm>({
    resolver: zodResolver(rwSchema),
    defaultValues: { device_type: "laptop", tunnel_mode: "split", group_ids: [], persistent_keepalive: 25 },
  });

  const selectedGroups = watch("group_ids") as number[];

  const onSubmit = async (data: RWForm) => {
    const res = await peersApi.createRoadWarrior(data);
    setCreatedPeer(res.data);
    setStep(3);
  };

  const steps = ["Info", "Network", "Groups", "Done"];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">New RoadWarrior</CardTitle>
        <CardDescription>
          <StepIndicator steps={steps} current={step} />
        </CardDescription>
      </CardHeader>
      <CardContent>
        {step < 3 ? (
          <form onSubmit={handleSubmit(onSubmit)}>
            {step === 0 && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label>Name / Device</Label>
                  <Input placeholder="Juan iPhone" {...register("name")} />
                  {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                </div>
                <div className="space-y-1">
                  <Label>Device Type</Label>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" {...register("device_type")}>
                    <option value="laptop">Laptop / Desktop</option>
                    <option value="ios">iOS</option>
                    <option value="android">Android</option>
                    <option value="server">Server</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <Label>Tunnel Mode</Label>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" {...register("tunnel_mode")}>
                    <option value="split">Split Tunnel (route only allowed zones)</option>
                    <option value="full">Full Tunnel (all traffic through VPN)</option>
                  </select>
                </div>
              </div>
            )}
            {step === 1 && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label>LAN Network (optional)</Label>
                  <p className="text-xs text-muted-foreground">Associate with a LAN network if this peer belongs to a branch office</p>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" {...register("network_id")}>
                    <option value="">None — VPN IP only</option>
                    {networks.filter(n => n.network_type === "lan").map((n) => <option key={n.id} value={n.id}>{n.name} ({n.subnet})</option>)}
                  </select>
                  {errors.network_id && <p className="text-xs text-destructive">{errors.network_id.message}</p>}
                </div>
                <div className="space-y-1">
                  <Label>DNS (optional)</Label>
                  <Input placeholder="10.10.10.10" {...register("dns")} />
                </div>
              </div>
            )}
            {step === 2 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Assign to groups to inherit access policies</p>
                {/* Hidden input to register group_ids with react-hook-form */}
                <input type="hidden" {...register("group_ids")} />
                <div className="space-y-2">
                  {groups.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No groups yet — peer will have no zone access</p>
                  ) : groups.map((g) => {
                    const checked = selectedGroups.includes(g.id);
                    return (
                      <label key={g.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            const next = checked
                              ? selectedGroups.filter((id) => id !== g.id)
                              : [...selectedGroups, g.id];
                            setValue("group_ids", next);
                          }}
                        />
                        <span className="text-sm font-mono">{g.name}</span>
                        {g.description && <span className="text-xs text-muted-foreground">— {g.description}</span>}
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-between mt-4">
              <div>
                {step > 0 && <Button type="button" variant="outline" size="sm" onClick={() => setStep(step - 1)}><ChevronLeft className="h-4 w-4" /> Back</Button>}
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
                {step < 2
                  ? <Button type="button" size="sm" onClick={() => setStep(step + 1)}>Next <ChevronRight className="h-4 w-4" /></Button>
                  : <Button type="submit" size="sm" disabled={isSubmitting}>{isSubmitting ? "Creating..." : "Create Peer"}</Button>
                }
              </div>
            </div>
          </form>
        ) : (
          createdPeer && (
            <div className="space-y-4">
              <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800">
                Peer <strong>{createdPeer.name}</strong> created — IP: <code>{createdPeer.assigned_ip}</code>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void downloadPeerConfigFile(createdPeer, "standard")}
                >
                  <Download className="h-4 w-4" /> Standard .conf
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void downloadPeerConfigFile(createdPeer, "mikrotik")}
                >
                  <Router className="h-4 w-4" /> MikroTik (.txt)
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowQr(true)}>
                  <QrCode className="h-4 w-4" /> View QR
                </Button>
                <Button size="sm" onClick={onDone}>Done</Button>
              </div>
            </div>
          )
        )}
      </CardContent>
      <QrCodeDialog peer={createdPeer} open={showQr} onOpenChange={setShowQr} />
    </Card>
  );
}

// ─── Branch Office Wizard ───────────────────────────────────────────────────

function BranchOfficeWizard({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [step, setStep] = useState(0);
  const [createdPeer, setCreatedPeer] = useState<Peer | null>(null);

  const { data: networks = [] } = useQuery({ queryKey: ["networks"], queryFn: () => networksApi.list().then((r) => r.data) });
  const { data: groups = [] } = useQuery({ queryKey: ["groups"], queryFn: () => groupsApi.list().then((r) => r.data) });

  const { register, handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm<BOForm>({
    resolver: zodResolver(boSchema),
    defaultValues: { device_type: "router", remote_subnets: [{ cidr: "" }], group_ids: [], persistent_keepalive: 25 },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "remote_subnets" });
  const selectedGroups = watch("group_ids") as number[];

  const onSubmit = async (data: BOForm) => {
    const res = await peersApi.createBranchOffice({
      ...data,
      remote_subnets: data.remote_subnets.map((s) => s.cidr),
    });
    setCreatedPeer(res.data);
    setStep(3);
  };

  const steps = ["Info", "Subnets", "Groups", "Done"];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">New Branch Office</CardTitle>
        <CardDescription><StepIndicator steps={steps} current={step} /></CardDescription>
      </CardHeader>
      <CardContent>
        {step < 3 ? (
          <form onSubmit={handleSubmit(onSubmit)}>
            {step === 0 && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label>Site Name</Label>
                  <Input placeholder="Sucursal Rosario" {...register("name")} />
                  {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                </div>
                <div className="space-y-1">
                  <Label>Router Type</Label>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" {...register("device_type")}>
                    <option value="router">Router (MikroTik, OPNsense, OpenWrt, Linux)</option>
                    <option value="server">Server</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <Label>LAN Network (optional)</Label>
                  <p className="text-xs text-muted-foreground">Associate with a LAN network if this peer belongs to a branch office</p>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" {...register("network_id")}>
                    <option value="">None — VPN IP only</option>
                    {networks.filter(n => n.network_type === "lan").map((n) => <option key={n.id} value={n.id}>{n.name} ({n.subnet})</option>)}
                  </select>
                  {errors.network_id && <p className="text-xs text-destructive">{errors.network_id.message}</p>}
                </div>
              </div>
            )}
            {step === 1 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">LAN subnets behind this router that the VPN should route</p>
                {fields.map((f, i) => (
                  <div key={f.id} className="flex gap-2">
                    <Input placeholder="192.168.50.0/24" {...register(`remote_subnets.${i}.cidr`)} />
                    {fields.length > 1 && (
                      <Button type="button" variant="ghost" size="icon" onClick={() => remove(i)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button type="button" variant="outline" size="sm" onClick={() => append({ cidr: "" })}>
                  <Plus className="h-4 w-4" /> Add Subnet
                </Button>
                <div className="space-y-1">
                  <Label>DNS (optional)</Label>
                  <Input placeholder="10.10.10.10" {...register("dns")} />
                </div>
              </div>
            )}
            {step === 2 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Assign to groups to define which central zones this branch can reach</p>
                {/* Hidden input to register group_ids with react-hook-form */}
                <input type="hidden" {...register("group_ids")} />
                <div className="space-y-2">
                  {groups.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No groups yet</p>
                  ) : groups.map((g) => {
                    const checked = selectedGroups.includes(g.id);
                    return (
                      <label key={g.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            const next = checked ? selectedGroups.filter((id) => id !== g.id) : [...selectedGroups, g.id];
                            setValue("group_ids", next);
                          }}
                        />
                        <span className="text-sm font-mono">{g.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-between mt-4">
              <div>
                {step > 0 && <Button type="button" variant="outline" size="sm" onClick={() => setStep(step - 1)}><ChevronLeft className="h-4 w-4" /> Back</Button>}
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
                {step < 2
                  ? <Button type="button" size="sm" onClick={() => setStep(step + 1)}>Next <ChevronRight className="h-4 w-4" /></Button>
                  : <Button type="submit" size="sm" disabled={isSubmitting}>{isSubmitting ? "Creating..." : "Create Peer"}</Button>
                }
              </div>
            </div>
          </form>
        ) : (
          createdPeer && (
            <div className="space-y-4">
              <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800">
                Branch office <strong>{createdPeer.name}</strong> created — VPN IP: <code>{createdPeer.assigned_ip}</code>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void downloadPeerConfigFile(createdPeer, "standard")}
                >
                  <Download className="h-4 w-4" /> Standard .conf
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void downloadPeerConfigFile(createdPeer, "mikrotik")}
                >
                  <Router className="h-4 w-4" /> MikroTik (.txt)
                </Button>
                <Button size="sm" onClick={onDone}>Done</Button>
              </div>
            </div>
          )
        )}
      </CardContent>
    </Card>
  );
}

function StepIndicator({ steps, current }: { steps: string[]; current: number }) {
  return (
    <div className="flex items-center gap-2 mt-1">
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${i === current ? "bg-primary text-primary-foreground" : i < current ? "bg-green-100 text-green-700" : "bg-muted text-muted-foreground"}`}>
            {s}
          </span>
          {i < steps.length - 1 && <span className="text-muted-foreground">›</span>}
        </div>
      ))}
    </div>
  );
}
