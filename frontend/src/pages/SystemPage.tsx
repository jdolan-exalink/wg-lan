import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { systemApi, type ServerConfigUpdate } from "@/api/system";
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
import { Copy, Check, RefreshCw, HardDrive, KeyRound, AlertTriangle, Save } from "lucide-react";

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handleCopy}
      className="ml-2 p-1 rounded hover:bg-accent text-muted-foreground"
      title="Copy to clipboard"
    >
      {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
    </button>
  );
}

function WarningDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  confirmLabel = "Confirm",
  confirmVariant = "destructive" as "destructive" | "default",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: React.ReactNode;
  onConfirm: () => void;
  confirmLabel?: string;
  confirmVariant?: "destructive" | "default";
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <DialogTitle>{title}</DialogTitle>
          </div>
          <DialogDescription className="pt-2">{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant={confirmVariant}
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function SystemPage() {
  const qc = useQueryClient();

  const { data: cfg, isLoading } = useQuery({
    queryKey: ["server-config"],
    queryFn: () => systemApi.getServerConfig().then((r) => r.data),
  });

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health().then((r) => r.data),
    refetchInterval: 10_000,
  });

  const { register, handleSubmit, reset, formState: { isDirty } } = useForm<ServerConfigUpdate>();

  const update = useMutation({
    mutationFn: (data: ServerConfigUpdate) => systemApi.updateServerConfig(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["server-config"] });
      reset();
    },
  });

  const applyConfig = useMutation({
    mutationFn: () => systemApi.applyConfig(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["server-config"] });
      qc.invalidateQueries({ queryKey: ["health"] });
    },
  });

  const wgUp = useMutation({
    mutationFn: () => systemApi.wgUp(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["health"] });
    },
  });

  const wgDown = useMutation({
    mutationFn: () => systemApi.wgDown(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["health"] });
    },
  });

  const wgRestart = useMutation({
    mutationFn: () => systemApi.wgRestart(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["health"] });
      qc.invalidateQueries({ queryKey: ["server-config"] });
    },
  });

  const regenerateKey = useMutation({
    mutationFn: () => systemApi.regenerateKey(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["server-config"] });
    },
  });

  const backup = useMutation({
    mutationFn: () => systemApi.backup(),
  });

  // Dialog states
  const [showSubnetDialog, setShowSubnetDialog] = useState(false);
  const [showPortDialog, setShowPortDialog] = useState(false);
  const [showRegenKeyDialog, setShowRegenKeyDialog] = useState(false);
  const [pendingSubnet, setPendingSubnet] = useState("");
  const [pendingPort, setPendingPort] = useState(0);

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (!cfg) return null;

  const disconnectWarning = (
    <div className="space-y-2">
      <p className="font-medium text-foreground">
        ⚠️ This action will disconnect all connected clients.
      </p>
      <p>
        All existing peer configuration files will need to be updated with the new settings.
        Clients will not be able to reconnect until their configs are regenerated.
      </p>
    </div>
  );

  const handleSubnetChange = (newSubnet: string) => {
    setPendingSubnet(newSubnet);
    setShowSubnetDialog(true);
  };

  const handlePortChange = (newPort: number) => {
    setPendingPort(newPort);
    setShowPortDialog(true);
  };

  const confirmSubnetChange = () => {
    update.mutate({ address: pendingSubnet });
  };

  const confirmPortChange = () => {
    update.mutate({ listen_port: pendingPort });
  };

  const confirmRegenerateKey = () => {
    regenerateKey.mutate();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Database</span>
            <Badge variant={health?.db === "ok" ? "default" : "destructive"}>
              {health?.db ?? "—"}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">WireGuard</span>
            <Badge variant={health?.wg_interface === "up" ? "default" : "secondary"}>
              {health?.wg_interface ?? "—"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Server Info */}
      <Card>
        <CardHeader>
          <CardTitle>Server Configuration</CardTitle>
          <CardDescription>
            Core WireGuard server settings. Changes require updating all peer config files.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground">Interface</Label>
            <p className="font-mono text-sm">{cfg.interface_name}</p>
          </div>

          {/* VPN Subnet - Editable */}
          <div>
            <Label className="text-xs text-muted-foreground">VPN Subnet (server address)</Label>
            <div className="flex items-center gap-2 mt-1">
              <p className="font-mono text-sm">{cfg.address}</p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => {
                  const val = prompt("Enter new VPN Subnet (e.g., 100.169.0.1/16):", cfg.address);
                  if (val && val !== cfg.address) {
                    handleSubnetChange(val);
                  }
                }}
              >
                Edit
              </Button>
            </div>
          </div>

          {/* Listen Port - Editable */}
          <div>
            <Label className="text-xs text-muted-foreground">Listen Port</Label>
            <div className="flex items-center gap-2 mt-1">
              <p className="font-mono text-sm">{cfg.listen_port}/udp</p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => {
                  const val = prompt("Enter new listen port (1-65535):", String(cfg.listen_port));
                  if (val) {
                    const port = parseInt(val, 10);
                    if (!isNaN(port) && port >= 1 && port <= 65535 && port !== cfg.listen_port) {
                      handlePortChange(port);
                    }
                  }
                }}
              >
                Edit
              </Button>
            </div>
          </div>

          {/* Public Key - Regenerable */}
          <div>
            <Label className="text-xs text-muted-foreground">Public Key</Label>
            <div className="flex items-center gap-2 mt-1">
              <p className="font-mono text-sm break-all flex-1">{cfg.public_key}</p>
              <CopyButton value={cfg.public_key} />
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => setShowRegenKeyDialog(true)}
              >
                <KeyRound className="h-3 w-3 mr-1" />
                Regenerate
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Editable settings */}
      <Card>
        <CardHeader>
          <CardTitle>Edit Settings</CardTitle>
          <CardDescription>Changes apply to new peer configs. Use "Apply Config" to push to WireGuard immediately.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((d) => update.mutate(d))} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="endpoint">Public Endpoint</Label>
              <Input
                id="endpoint"
                placeholder={cfg.endpoint}
                defaultValue={cfg.endpoint}
                {...register("endpoint")}
              />
              <p className="text-xs text-muted-foreground">Hostname or IP peers use to connect (e.g. vpn.example.com)</p>
            </div>
            <div className="space-y-1">
              <Label htmlFor="dns">DNS (optional)</Label>
              <Input
                id="dns"
                placeholder="1.1.1.1, 8.8.8.8"
                defaultValue={cfg.dns ?? ""}
                {...register("dns")}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="mtu">MTU (optional)</Label>
              <Input
                id="mtu"
                type="number"
                placeholder="1420"
                defaultValue={cfg.mtu ?? 1420}
                {...register("mtu", { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="post_up">PostUp</Label>
              <Input id="post_up" defaultValue={cfg.post_up ?? ""} {...register("post_up")} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="post_down">PostDown</Label>
              <Input id="post_down" defaultValue={cfg.post_down ?? ""} {...register("post_down")} />
            </div>
            <Button type="submit" disabled={update.isPending || !isDirty}>
              <Save className="h-4 w-4 mr-2" />
              {update.isPending ? "Saving..." : "Save Changes"}
            </Button>
            {update.isSuccess && <span className="ml-3 text-sm text-green-600">Saved.</span>}
            {update.isError && <span className="ml-3 text-sm text-destructive">Error saving.</span>}
          </form>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>Manage WireGuard interface and backups</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={() => applyConfig.mutate()}
            disabled={applyConfig.isPending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {applyConfig.isPending ? "Applying..." : "Apply Config"}
          </Button>
          <Button
            variant="default"
            onClick={() => {
              applyConfig.mutate(undefined, {
                onSuccess: () => wgRestart.mutate(),
              });
            }}
            disabled={applyConfig.isPending || wgRestart.isPending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {applyConfig.isPending || wgRestart.isPending ? "Applying & Restarting..." : "Apply Config & Restart WG"}
          </Button>
          <Button
            variant="outline"
            onClick={() => wgUp.mutate()}
            disabled={wgUp.isPending || health?.wg_interface === "up"}
          >
            WG Up
          </Button>
          <Button
            variant="outline"
            onClick={() => wgDown.mutate()}
            disabled={wgDown.isPending || health?.wg_interface === "down"}
          >
            WG Down
          </Button>
          <Button
            variant="outline"
            onClick={() => backup.mutate()}
            disabled={backup.isPending}
          >
            <HardDrive className="h-4 w-4 mr-2" />
            {backup.isPending ? "Backing up..." : "Backup DB"}
          </Button>
          {backup.isSuccess && (
            <span className="text-sm text-green-600 self-center">
              Backup saved: {(backup.data as any)?.data?.path}
            </span>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialogs */}
      <WarningDialog
        open={showSubnetDialog}
        onOpenChange={setShowSubnetDialog}
        title="Change VPN Subnet"
        description={disconnectWarning}
        onConfirm={confirmSubnetChange}
        confirmLabel="Change Subnet"
      />

      <WarningDialog
        open={showPortDialog}
        onOpenChange={setShowPortDialog}
        title="Change Listen Port"
        description={disconnectWarning}
        onConfirm={confirmPortChange}
        confirmLabel="Change Port"
      />

      <WarningDialog
        open={showRegenKeyDialog}
        onOpenChange={setShowRegenKeyDialog}
        title="Regenerate Server Keypair"
        description={
          <div className="space-y-2">
            <p className="font-medium text-foreground">
              ⚠️ This will generate a new server keypair and disconnect all clients.
            </p>
            <p>
              All peer configuration files must be regenerated with the new public key.
              Existing peers will not be able to connect until their configs are updated.
            </p>
          </div>
        }
        onConfirm={confirmRegenerateKey}
        confirmLabel="Regenerate Key"
      />
    </div>
  );
}
