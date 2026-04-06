import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { systemApi, type ServerConfigUpdate, type ADConfigUpdate, type ADGroupMapping, type ADGroupMappingCreate, type ADGroupFromAD } from "@/api/system";
import { speedTestApi } from "@/api/speedtest";
import { groupsApi } from "@/api/networks";
import { authApi } from "@/api/auth";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Copy, Check, KeyRound, Users, FolderSync, Link, Plus, X, RefreshCw, Trash2, Search, Zap, Gauge, ArrowDownToLine, ArrowUpToLine, Clock } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ─── AD Configuration Tab ───────────────────────────────────────────────────────

function ADConfigurationTab() {
  const qc = useQueryClient();
  const { data: adConfig } = useQuery({
    queryKey: ["ad-config"],
    queryFn: () => systemApi.getADConfig().then((r) => r.data),
  });

  const { data: adGroups = [] } = useQuery({
    queryKey: ["ad-groups-from-server"],
    queryFn: () => systemApi.getADGroupsFromServer().then((r) => r.data.groups),
    enabled: !!adConfig?.ad_enabled,
  });

  const { data: mappings = [] } = useQuery({
    queryKey: ["ad-group-mappings"],
    queryFn: () => systemApi.getADGroupMappings().then((r) => r.data),
  });

  const { data: netloomGroups = [] } = useQuery({
    queryKey: ["netloom-groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const {
    register: regAD,
    handleSubmit: handleADSubmit,
    setValue: setADValue,
    watch: watchAD,
    reset: resetAD,
  } = useForm<ADConfigUpdate>();

  useEffect(() => {
    if (adConfig) {
      resetAD({
        ad_enabled: adConfig.ad_enabled,
        ad_server: adConfig.ad_server ?? "",
        ad_server_backup: adConfig.ad_server_backup ?? "",
        ad_base_dn: adConfig.ad_base_dn ?? "",
        ad_bind_dn: adConfig.ad_bind_dn ?? "",
        ad_user_filter: adConfig.ad_user_filter ?? "",
        ad_group_filter: adConfig.ad_group_filter ?? "",
        ad_use_ssl: adConfig.ad_use_ssl,
        ad_require_membership: adConfig.ad_require_membership,
      });
    }
  }, [adConfig, resetAD]);

  const updateAD = useMutation({
    mutationFn: (data: ADConfigUpdate) => systemApi.updateADConfig(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ad-config"] }),
  });

  const testConnection = useMutation({
    mutationFn: () => systemApi.testADConnection(),
  });

  const refreshADGroups = useMutation({
    mutationFn: () => {
      console.log("Refreshing AD groups...");
      return systemApi.getADGroupsFromServer();
    },
    onSuccess: (res) => {
      console.log("AD Groups response:", res.data);
      qc.setQueryData(["ad-groups-from-server"], res.data.groups);
      setRefreshSuccess(`${res.data.groups.length} AD groups found`);
      setTimeout(() => setRefreshSuccess(null), 3000);
    },
    onError: (err) => {
      console.log("AD Groups error:", err);
      setRefreshSuccess("Failed to fetch AD groups");
      setTimeout(() => setRefreshSuccess(null), 3000);
    },
  });

  const createMapping = useMutation({
    mutationFn: (data: ADGroupMappingCreate) => systemApi.createADGroupMapping(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ad-group-mappings"] }),
  });

  const deleteMapping = useMutation({
    mutationFn: (id: number) => systemApi.deleteADGroupMapping(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ad-group-mappings"] }),
  });

  const createNetloomGroup = useMutation({
    mutationFn: (data: { name: string; description?: string }) => groupsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["netloom-groups"] });
      setShowNewGroupDialog(false);
      setNewGroupName("");
    },
  });

  const [showMappingForm, setShowMappingForm] = useState(false);
  const [newMapping, setNewMapping] = useState<{ ad_group_dn: string; ad_group_name: string; netloom_group_id: number } | null>(null);
  const [mappingSuccess, setMappingSuccess] = useState(false);
  const [refreshSuccess, setRefreshSuccess] = useState<string | null>(null);
  const [adGroupSearch, setAdGroupSearch] = useState("");
  const [showNewGroupDialog, setShowNewGroupDialog] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");

  const handleCreateMapping = () => {
    if (newMapping) {
      createMapping.mutate(newMapping, {
        onSuccess: () => {
          setShowMappingForm(false);
          setNewMapping(null);
          setMappingSuccess(true);
          setTimeout(() => setMappingSuccess(false), 3000);
        },
      });
    }
  };

  if (!adConfig) return <p className="text-sm text-on-surface-variant">Loading...</p>;

  return (
    <div className="space-y-6">
      {/* AD Enable/Disable */}
      <section className="bg-surface-container rounded-xl p-8 border border-outline-variant/10">
        <header className="mb-6">
          <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            Active Directory Integration
          </h3>
          <p className="text-sm text-on-surface-variant mt-1">
            Configure LDAP/AD authentication and group mapping
          </p>
        </header>

        <form onSubmit={handleADSubmit((d) => updateAD.mutate(d))} className="space-y-6">
          {/* Enable AD */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setADValue("ad_enabled", !watchAD("ad_enabled"))}
              className={cn(
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                watchAD("ad_enabled") ? "bg-primary" : "bg-surface-container-high"
              )}
            >
              <span
                className={cn(
                  "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                  watchAD("ad_enabled") ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
            <span className="text-sm font-medium">Enable Active Directory Authentication</span>
          </div>

          {watchAD("ad_enabled") && (
            <>
              {/* AD Server URL */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  AD Server URL (Primary)
                </label>
                <Input
                  {...regAD("ad_server")}
                  placeholder="ldaps://192.168.1.10:636"
                  className="max-w-md"
                />
              </div>

              {/* AD Server Backup URL */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  AD Server URL (Backup)
                </label>
                <Input
                  {...regAD("ad_server_backup")}
                  placeholder="ldaps://192.168.1.20:636 (optional)"
                  className="max-w-md"
                />
              </div>

              {/* Base DN */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Base DN
                </label>
                <Input
                  {...regAD("ad_base_dn")}
                  placeholder="DC=empresa,DC=local"
                  className="max-w-md"
                />
              </div>

              {/* Bind DN - Formato DOMAIN\username */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Bind Username (Service Account)
                </label>
                <Input
                  {...regAD("ad_bind_dn")}
                  placeholder="EMPRESA\Administrador"
                  className="max-w-md"
                />
                <p className="text-[11px] text-on-surface-variant mt-1">Format: DOMAIN\username</p>
              </div>

              {/* Bind Password */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Bind Password
                </label>
                <Input
                  {...regAD("ad_bind_password")}
                  type="password"
                  placeholder="••••••••••••"
                  className="max-w-md"
                />
              </div>

              {/* User Filter - Opciones predefinidas */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  User Filter
                </label>
                <select
                  {...regAD("ad_user_filter")}
                  className="w-full max-w-md h-10 px-3 rounded-lg border border-input bg-background focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <option value="(sAMAccountName={username})">Default: sAMAccountName = username</option>
                  <option value="(userPrincipalName={username})">UPN: userPrincipalName = username</option>
                  <option value="(mail={username})">Email: mail = username</option>
                  <option value="(employeeId={username})">Employee ID: employeeId = username</option>
                  <option value="(sAMAccountName=*{username}*)">Contains: sAMAccountName contains username</option>
                </select>
                <p className="text-[11px] text-on-surface-variant mt-1">Use {"{username}"} placeholder</p>
              </div>

              {/* Use SSL */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setADValue("ad_use_ssl", !watchAD("ad_use_ssl"))}
                  className={cn(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    watchAD("ad_use_ssl") ? "bg-primary" : "bg-surface-container-high"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      watchAD("ad_use_ssl") ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
                <span className="text-sm font-medium">Use LDAPS (SSL/TLS)</span>
              </div>

              {/* Require Membership */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setADValue("ad_require_membership", !watchAD("ad_require_membership"))}
                  className={cn(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    watchAD("ad_require_membership") ? "bg-primary" : "bg-surface-container-high"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      watchAD("ad_require_membership") ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
                <span className="text-sm font-medium">Require AD Group Membership</span>
                <span className="text-xs text-on-surface-variant">(Deny access if user not in mapped AD group)</span>
              </div>

              {/* Test Connection */}
              <div className="flex items-center gap-4 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => testConnection.mutate()}
                  disabled={testConnection.isPending}
                >
                  <Link className="h-4 w-4 mr-2" />
                  {testConnection.isPending ? "Testing..." : "Test Connection"}
                </Button>
                {testConnection.isSuccess && (
                  <span className={cn(
                    "text-sm font-medium",
                    testConnection.data.data?.success ? "text-secondary" : "text-error"
                  )}>
                    {testConnection.data.data?.success ? testConnection.data.data.message : testConnection.data.data?.error}
                  </span>
                )}
              </div>
            </>
          )}

          {/* Save */}
          <div className="flex items-center gap-4 pt-2">
            <Button type="submit" disabled={updateAD.isPending}>
              {updateAD.isPending ? "Saving..." : "Save Configuration"}
            </Button>
            {updateAD.isSuccess && <span className="text-sm text-secondary font-medium">Saved.</span>}
            {updateAD.isError && <span className="text-sm text-error">Error saving.</span>}
          </div>
        </form>
      </section>

      {/* Group Mappings */}
      {adConfig.ad_enabled && (
        <section className="bg-surface-container rounded-xl p-8 border border-outline-variant/10">
          <header className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                <FolderSync className="h-5 w-5 text-primary" />
                Group Mappings
              </h3>
              <p className="text-sm text-on-surface-variant mt-1">
                Map AD groups to NetLoom internal groups
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refreshADGroups.mutate()}
                disabled={refreshADGroups.isPending}
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", refreshADGroups.isPending && "animate-spin")} />
                Refresh AD Groups
              </Button>
              <Button size="sm" onClick={() => setShowMappingForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Mapping
              </Button>
            </div>
          </header>

          {refreshSuccess && (
            <div className={cn(
              "mb-4 p-3 rounded-lg text-sm",
              refreshSuccess.startsWith("Failed")
                ? "bg-error/10 text-error"
                : "bg-secondary/10 text-secondary"
            )}>
              {refreshSuccess}
            </div>
          )}

          {mappingSuccess && (
            <div className="mb-4 p-3 bg-secondary/10 text-secondary rounded-lg text-sm">
              Mapping created successfully!
            </div>
          )}

          {/* Mappings Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-outline-variant/20">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-on-surface-variant uppercase">AD Group</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-on-surface-variant uppercase">NetLoom Group</th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-on-surface-variant uppercase">Enabled</th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-on-surface-variant uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {mappings.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-on-surface-variant">
                      No mappings configured. Add a mapping to connect AD groups to NetLoom groups.
                    </td>
                  </tr>
                ) : (
                  mappings.map((m) => (
                    <tr key={m.id} className="border-b border-outline-variant/10 hover:bg-surface-container-high/50">
                      <td className="py-3 px-4">
                        <div className="font-medium">{m.ad_group_name}</div>
                        <div className="text-xs text-on-surface-variant font-mono">{m.ad_group_dn}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {m.netloom_group_name ?? `Group #${m.netloom_group_id}`}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => systemApi.updateADGroupMapping(m.id, { enabled: !m.enabled }).then(() => qc.invalidateQueries({ queryKey: ["ad-group-mappings"] }))}
                          className={cn(
                            "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
                            m.enabled ? "bg-primary" : "bg-surface-container-high"
                          )}
                        >
                          <span
                            className={cn(
                              "inline-block h-3 w-3 transform rounded-full bg-white transition-transform",
                              m.enabled ? "translate-x-5" : "translate-x-1"
                            )}
                          />
                        </button>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-error hover:bg-error/10"
                          onClick={() => deleteMapping.mutate(m.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Add Mapping Dialog */}
      <Dialog open={showMappingForm} onOpenChange={(open) => { setShowMappingForm(open); if (!open) { setNewMapping(null); setAdGroupSearch(""); } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add AD Group Mapping</DialogTitle>
            <DialogDescription>
              Select an AD group and map it to a NetLoom group
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">AD Group</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search groups..."
                  value={adGroupSearch}
                  onChange={(e) => setAdGroupSearch(e.target.value)}
                  className="w-full h-10 pl-9 px-3 rounded-lg border border-input bg-background focus-visible:ring-2 focus-visible:ring-primary text-sm"
                />
              </div>
              <select
                className="w-full h-32 px-3 rounded-lg border border-input bg-background focus-visible:ring-2 focus-visible:ring-primary text-sm"
                size={8}
                onChange={(e) => {
                  const selected = adGroups.find(g => g.dn === e.target.value);
                  if (selected) {
                    setNewMapping({ ad_group_dn: selected.dn, ad_group_name: selected.name, netloom_group_id: newMapping?.netloom_group_id ?? 0 });
                  }
                }}
                value={newMapping?.ad_group_dn ?? ""}
              >
                {[...adGroups]
                  .filter(g =>
                    g.name.toLowerCase().includes(adGroupSearch.toLowerCase()) ||
                    g.sam_name.toLowerCase().includes(adGroupSearch.toLowerCase())
                  )
                  .sort((a, b) => a.name.localeCompare(b.name))
                  .map((g) => (
                    <option key={g.dn} value={g.dn}>{g.name} ({g.sam_name})</option>
                  ))}
              </select>
              {adGroupSearch && [...adGroups].filter(g =>
                g.name.toLowerCase().includes(adGroupSearch.toLowerCase()) ||
                g.sam_name.toLowerCase().includes(adGroupSearch.toLowerCase())
              ).length === 0 && (
                <p className="text-xs text-on-surface-variant">No groups match "{adGroupSearch}"</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">NetLoom Group</label>
              <div className="flex gap-2">
                <Select
                  value={newMapping?.netloom_group_id?.toString() ?? ""}
                  onValueChange={(value) => {
                    if (value === "__new__") {
                      setShowNewGroupDialog(true);
                      return;
                    }
                    if (newMapping) {
                      setNewMapping({ ...newMapping, netloom_group_id: parseInt(value) });
                    }
                  }}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a NetLoom group..." />
                  </SelectTrigger>
                  <SelectContent>
                    {netloomGroups.map((g) => (
                      <SelectItem key={g.id} value={g.id.toString()}>{g.name}</SelectItem>
                    ))}
                    <SelectItem value="__new__">+ Create new group...</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowMappingForm(false); setNewMapping(null); setAdGroupSearch(""); }}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateMapping}
              disabled={!newMapping?.ad_group_dn || !newMapping?.netloom_group_id || createMapping.isPending}
            >
              {createMapping.isPending ? "Creating..." : "Create Mapping"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create New NetLoom Group Dialog */}
      <Dialog open={showNewGroupDialog} onOpenChange={(open) => { setShowNewGroupDialog(open); if (!open) setNewGroupName(""); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Group</DialogTitle>
            <DialogDescription>
              Enter a name for the new NetLoom group
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <Input
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="Group name"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newGroupName.trim()) {
                  createNetloomGroup.mutate({ name: newGroupName.trim() }, {
                    onSuccess: (res) => {
                      const newId = res.data.id;
                      setNewMapping((prev) => prev ? { ...prev, netloom_group_id: newId } : null);
                    },
                  });
                }
              }}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowNewGroupDialog(false); setNewGroupName(""); }}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (newGroupName.trim()) {
                  createNetloomGroup.mutate({ name: newGroupName.trim() }, {
                    onSuccess: (res) => {
                      const newId = res.data.id;
                      setNewMapping((prev) => prev ? { ...prev, netloom_group_id: newId } : null);
                    },
                  });
                }
              }}
              disabled={!newGroupName.trim() || createNetloomGroup.isPending}
            >
              {createNetloomGroup.isPending ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Utilities ──────────────────────────────────────────────────────────────────

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

// ─── Small reusable pieces ────────────────────────────────────────────────────

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="p-1 rounded hover:bg-surface-container text-outline transition-colors"
      title="Copy"
    >
      {copied ? <Check className="h-4 w-4 text-secondary" /> : <Copy className="h-4 w-4" />}
    </button>
  );
}

function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  confirmLabel = "Confirm",
  danger = false,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  description: React.ReactNode;
  onConfirm: () => void;
  confirmLabel?: string;
  danger?: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription asChild>
            <div className="pt-1 text-sm text-on-surface-variant">{description}</div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant={danger ? "destructive" : "default"}
            onClick={() => { onConfirm(); onOpenChange(false); }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─── Donut gauge ──────────────────────────────────────────────────────────────

function DonutGauge({ percent, colorClass, icon }: { percent: number; colorClass: string; icon: string }) {
  const CIRC = 251.2;
  const dashOffset = CIRC * (1 - Math.min(100, Math.max(0, percent)) / 100);
  return (
    <div className="relative w-24 h-24 flex-shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r="40" fill="transparent" strokeWidth="8"
          stroke="currentColor" className="text-surface-container" />
        <circle cx="48" cy="48" r="40" fill="transparent" strokeWidth="8"
          stroke="currentColor" strokeDasharray={CIRC} strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className={`transition-all duration-700 ${colorClass}`} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className={`material-symbols-outlined text-3xl ${colorClass}`}
          style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
        >
          {icon}
        </span>
      </div>
    </div>
  );
}

// ─── Sparkline bar chart ──────────────────────────────────────────────────────

function Sparkline({ data, colorClass }: { data: number[]; colorClass: string }) {
  const BARS = 12;
  const max = Math.max(...data, 1);
  const padded = [...Array(Math.max(0, BARS - data.length)).fill(0), ...data.slice(-BARS)];
  return (
    <div className="flex gap-0.5 items-end h-12 mt-3">
      {padded.map((v, i) => {
        const h = Math.max(3, Math.round((v / max) * 48));
        const opacity = v === 0 ? "opacity-10" : i === padded.length - 1 ? "opacity-100" : "opacity-50";
        return (
          <div
            key={i}
            className={`w-1 rounded-full ${colorClass} ${opacity} transition-all duration-300`}
            style={{ height: h }}
          />
        );
      })}
    </div>
  );
}

// ─── Password change form ─────────────────────────────────────────────────────

function PasswordChangeForm() {
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<{
    current_password: string;
    new_password: string;
    confirm_password: string;
  }>();
  const newPwd = watch("new_password");
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      authApi.changePassword(current_password, new_password),
    onSuccess: () => {
      setSuccess(true);
      setServerError(null);
      reset();
      setTimeout(() => setSuccess(false), 3000);
    },
    onError: (err: any) => {
      setServerError(err?.response?.data?.detail ?? "Failed to update password");
    },
  });

  return (
    <form
      onSubmit={handleSubmit((d) =>
        mutation.mutate({ current_password: d.current_password, new_password: d.new_password })
      )}
      className="space-y-5 max-w-lg"
    >
      <div className="space-y-1.5">
        <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant pl-1">
          Current Password
        </label>
        <Input
          type="password"
          placeholder="••••••••••••"
          className="h-12 bg-surface border-none focus-visible:ring-primary"
          {...register("current_password", { required: true })}
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant pl-1">
            New Password
          </label>
          <Input
            type="password"
            placeholder="New password"
            className="h-12 bg-surface border-none focus-visible:ring-primary"
            {...register("new_password", { required: true, minLength: 8 })}
          />
          {errors.new_password?.type === "minLength" && (
            <p className="text-xs text-error pl-1">Minimum 8 characters</p>
          )}
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant pl-1">
            Confirm Password
          </label>
          <Input
            type="password"
            placeholder="Repeat password"
            className="h-12 bg-surface border-none focus-visible:ring-primary"
            {...register("confirm_password", {
              required: true,
              validate: (v) => v === newPwd || "Passwords do not match",
            })}
          />
          {errors.confirm_password && (
            <p className="text-xs text-error pl-1">{errors.confirm_password.message}</p>
          )}
        </div>
      </div>
      {serverError && <p className="text-sm text-error">{serverError}</p>}
      <div className="pt-2 flex items-center gap-4">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-primary text-on-primary font-bold py-3 px-8 rounded-full shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-60"
        >
          {mutation.isPending ? "Updating…" : "Update Password"}
        </button>
        {success && <span className="text-sm text-secondary font-medium">Password updated!</span>}
      </div>
    </form>
  );
}

// ─── Speed Test Tab ───────────────────────────────────────────────────────────

type TestPhase = "idle" | "ping" | "download" | "upload" | "done" | "error";
type TestMode = "full" | "ping" | "download" | "upload";

function SpeedTestTab() {
  const [phase, setPhase] = useState<TestPhase>("idle");
  const [testMode, setTestMode] = useState<TestMode>("full");
  const [pingMs, setPingMs] = useState<number | null>(null);
  const [jitterMs, setJitterMs] = useState<number | null>(null);
  const [dlSpeed, setDlSpeed] = useState(0);
  const [ulSpeed, setUlSpeed] = useState(0);
  const [finalDl, setFinalDl] = useState(0);
  const [finalUl, setFinalUl] = useState(0);
  const [qualityScore, setQualityScore] = useState(0);
  const [qualityLabel, setQualityLabel] = useState("");
  const [gaugeValue, setGaugeValue] = useState(0);
  const [gaugeLabel, setGaugeLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-tertiary";
    if (score >= 75) return "text-primary";
    if (score >= 50) return "text-yellow-500";
    if (score >= 25) return "text-orange-500";
    return "text-error";
  };

  const calcQuality = (p: number, d: number, u: number): [number, string] => {
    let s = 100;
    if (p <= 20) s -= 0;
    else if (p <= 50) s -= 10;
    else if (p <= 100) s -= 25;
    else if (p <= 200) s -= 40;
    else s -= 60;

    if (d >= 100) s -= 0;
    else if (d >= 50) s -= 5;
    else if (d >= 10) s -= 15;
    else if (d >= 1) s -= 25;
    else s -= 35;

    if (u >= 50) s -= 0;
    else if (u >= 20) s -= 5;
    else if (u >= 5) s -= 15;
    else if (u >= 1) s -= 25;
    else s -= 30;

    s = Math.max(0, Math.min(100, s));
    const label = s >= 90 ? "Excellent" : s >= 75 ? "Good" : s >= 50 ? "Fair" : s >= 25 ? "Poor" : "Bad";
    return [s, label];
  };

  const runPing = async () => {
    setPhase("ping");
    const pings: number[] = [];
    for (let i = 0; i < 20; i++) {
      const t0 = performance.now();
      await speedTestApi.ping();
      const elapsed = performance.now() - t0;
      pings.push(elapsed);
      setPingMs(Math.round(pings.reduce((a, b) => a + b, 0) / pings.length * 10) / 10);
      setGaugeValue(Math.round(elapsed));
      setGaugeLabel("PING");
    }
    if (pings.length > 1) {
      const mean = pings.reduce((a, b) => a + b, 0) / pings.length;
      const jitter = Math.sqrt(pings.reduce((s, v) => s + (v - mean) ** 2, 0) / pings.length);
      setJitterMs(Math.round(jitter * 10) / 10);
    }
    return pingMs ?? 0;
  };

  const runDownload = async () => {
    setPhase("download");
    setDlSpeed(0);
    const dlSizes = [10_000_000, 100_000_000];
    let bestDl = 0;
    for (const size of dlSizes) {
      const t0 = performance.now();
      const res = await speedTestApi.download(size);
      const elapsed = (performance.now() - t0) / 1000;
      const bytes = (res.data as ArrayBuffer).byteLength;
      const mbps = (bytes * 8) / elapsed / 1_000_000;
      if (mbps > bestDl) bestDl = mbps;
      setDlSpeed(Math.round(mbps * 10) / 10);
      setGaugeValue(Math.round(mbps));
      setGaugeLabel("DOWNLOAD");
    }
    setFinalDl(Math.round(bestDl * 10) / 10);
    return bestDl;
  };

  const runUpload = async () => {
    setPhase("upload");
    setUlSpeed(0);
    const ulSizes = [10_000_000, 100_000_000];
    let bestUl = 0;
    for (const size of ulSizes) {
      const data = new ArrayBuffer(size);
      const t0 = performance.now();
      await speedTestApi.upload(data);
      const elapsed = (performance.now() - t0) / 1000;
      const mbps = (size * 8) / elapsed / 1_000_000;
      if (mbps > bestUl) bestUl = mbps;
      setUlSpeed(Math.round(mbps * 10) / 10);
      setGaugeValue(Math.round(mbps));
      setGaugeLabel("UPLOAD");
    }
    setFinalUl(Math.round(bestUl * 10) / 10);
    return bestUl;
  };

  const runTest = async () => {
    setIsRunning(true);
    setPingMs(null);
    setJitterMs(null);
    setDlSpeed(0);
    setUlSpeed(0);
    setFinalDl(0);
    setFinalUl(0);
    setGaugeValue(0);
    setGaugeLabel("");
    setError(null);

    try {
      if (testMode === "ping") {
        await runPing();
        setPhase("done");
        setGaugeValue(pingMs ?? 0);
        setGaugeLabel("PING ms");
      } else if (testMode === "download") {
        const bestDl = await runDownload();
        setPhase("done");
        setGaugeValue(Math.round(bestDl));
        setGaugeLabel("Mbps");
      } else if (testMode === "upload") {
        const bestUl = await runUpload();
        setPhase("done");
        setGaugeValue(Math.round(bestUl));
        setGaugeLabel("Mbps");
      } else {
        const p = await runPing();
        const d = await runDownload();
        const u = await runUpload();
        const [score, label] = calcQuality(p, d, u);
        setPhase("done");
        setQualityScore(score);
        setQualityLabel(label);
        setGaugeValue(score);
        setGaugeLabel(label);
      }
    } catch {
      setPhase("error");
      setError("Test failed. Check your connection.");
    } finally {
      setIsRunning(false);
    }
  };

  const circumference = 2 * Math.PI * 120;
  const gaugeOffset = circumference - (gaugeValue / 200) * circumference;

  const showPhase = (p: string) => {
    if (testMode === "full") return true;
    if (testMode === "ping" && p === "ping") return true;
    if (testMode === "download" && p === "download") return true;
    if (testMode === "upload" && p === "upload") return true;
    return false;
  };

  return (
    <div className="flex flex-col items-center space-y-6 py-4">
      {/* Gauge */}
      <div className="relative w-64 h-64 md:w-80 md:h-80">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 280 280">
          <circle
            cx="140" cy="140" r="120"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            className="text-on-surface/5"
          />
          <circle
            cx="140" cy="140" r="120"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={gaugeOffset}
            strokeLinecap="round"
            className={cn(
              "transition-all duration-500",
              phase === "ping" ? "text-primary" :
              phase === "download" ? "text-tertiary" :
              phase === "upload" ? "text-secondary" :
              phase === "done" ? getScoreColor(qualityScore) :
              "text-error"
            )}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {phase === "idle" && (
            <>
              <Zap className="w-8 h-8 text-on-surface-variant mb-2" />
              <span className="text-sm text-on-surface-variant">Ready</span>
            </>
          )}
          {(phase === "ping" || phase === "download" || phase === "upload") && (
            <>
              <span className={cn(
                "text-4xl md:text-5xl font-bold",
                phase === "ping" ? "text-primary" :
                phase === "download" ? "text-tertiary" : "text-secondary"
              )}>
                {gaugeValue}
              </span>
              <span className="text-sm text-on-surface-variant mt-1">
                {phase === "ping" ? "ms" : "Mbps"}
              </span>
              <span className="text-xs text-on-surface-variant/60 mt-1 uppercase tracking-wider">
                {gaugeLabel}
              </span>
            </>
          )}
          {phase === "done" && (
            <>
              <span className={cn("text-4xl md:text-5xl font-bold", getScoreColor(qualityScore))}>
                {qualityScore}
              </span>
              <span className="text-sm text-on-surface-variant mt-1">/ 100</span>
              <span className={cn("text-sm font-medium mt-1", getScoreColor(qualityScore))}>
                {qualityLabel}
              </span>
            </>
          )}
          {phase === "error" && (
            <>
              <span className="text-2xl font-bold text-error">Error</span>
              <span className="text-xs text-on-surface-variant mt-1">{error}</span>
            </>
          )}
        </div>
      </div>

      {/* Phase indicator */}
      <div className="flex items-center gap-3">
        {(["ping", "download", "upload"] as const).map((p) => (
          <div key={p} className={cn("flex items-center gap-2", !showPhase(p) && "opacity-30")}>
            <div className={cn(
              "w-2 h-2 rounded-full",
              phase === p ? "bg-primary animate-pulse" :
              (p === "ping" && (phase === "download" || phase === "upload" || phase === "done")) ? "bg-tertiary" :
              (p === "download" && (phase === "upload" || phase === "done")) ? "bg-secondary" :
              "bg-on-surface/10"
            )} />
            <span className={cn(
              "text-xs font-medium uppercase tracking-wider",
              phase === p ? "text-primary" :
              (p === "ping" && (phase === "download" || phase === "upload" || phase === "done")) ? "text-tertiary" :
              (p === "download" && (phase === "upload" || phase === "done")) ? "text-secondary" :
              "text-on-surface-variant/40"
            )}>
              {p === "ping" ? "Ping" : p === "download" ? "Download" : "Upload"}
            </span>
          </div>
        ))}
      </div>

      {/* Results */}
      {(phase === "done" || phase === "error") && (
        <div className="grid grid-cols-3 gap-4 w-full max-w-lg">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary">
              {pingMs !== null ? `${pingMs}` : "—"}
            </p>
            <p className="text-xs text-on-surface-variant">ms ping</p>
            {jitterMs !== null && (
              <p className="text-[10px] text-on-surface-variant/60">±{jitterMs} jitter</p>
            )}
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-tertiary">
              {finalDl > 0 ? `${finalDl}` : "—"}
            </p>
            <p className="text-xs text-on-surface-variant">Mbps down</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-secondary">
              {finalUl > 0 ? `${finalUl}` : "—"}
            </p>
            <p className="text-xs text-on-surface-variant">Mbps up</p>
          </div>
        </div>
      )}

      {/* Test mode selector + Run button */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1 bg-surface-container rounded-lg p-1">
          {([
            { value: "full" as TestMode, label: "Full" },
            { value: "ping" as TestMode, label: "Ping" },
            { value: "download" as TestMode, label: "Download" },
            { value: "upload" as TestMode, label: "Upload" },
          ]).map((m) => (
            <button
              key={m.value}
              onClick={() => setTestMode(m.value)}
              disabled={isRunning}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-all",
                testMode === m.value
                  ? "bg-primary-container text-on-primary-container"
                  : "text-outline-variant hover:text-on-surface-variant"
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
        <button
          onClick={runTest}
          disabled={isRunning}
          className="px-6 py-2 bg-tertiary text-white text-sm font-bold rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2 disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Testing...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Run Test
            </>
          )}
        </button>
      </div>

      {/* Rerun button */}
      {(phase === "done" || phase === "error") && (
        <button
          onClick={runTest}
          className="px-6 py-2 bg-tertiary text-white text-sm font-bold rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Run Again
        </button>
      )}

      {/* API Info */}
      <section className="w-full max-w-lg bg-surface-container rounded-xl p-4 border border-outline-variant/10">
        <h4 className="text-sm font-bold text-on-surface mb-2 flex items-center gap-1">
          <Gauge className="w-3 h-3 text-primary" />
          API Endpoints
        </h4>
        <div className="space-y-1">
          <p className="text-[10px] font-mono text-on-surface-variant">GET  /api/speedtest/ping</p>
          <p className="text-[10px] font-mono text-on-surface-variant">GET  /api/speedtest/download?size=N</p>
          <p className="text-[10px] font-mono text-on-surface-variant">POST /api/speedtest/upload</p>
        </div>
      </section>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function SystemPage() {
  const qc = useQueryClient();
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<"monitor" | "general" | "ad" | "test">("monitor");

  const normalizeServerConfigUpdate = (data: ServerConfigUpdate): ServerConfigUpdate => ({
    ...data,
    address: data.address?.trim() || undefined,
    endpoint: data.endpoint?.trim() || undefined,
    dns: data.dns?.trim() ? data.dns.trim() : null,
    post_up: data.post_up?.trim() ? data.post_up.trim() : null,
    post_down: data.post_down?.trim() ? data.post_down.trim() : null,
    vpn_domain: data.vpn_domain?.trim() ? data.vpn_domain.trim() : null,
  });

  // ── Data queries ──────────────────────────────────────────────────────────

  const { data: cfg, isLoading } = useQuery({
    queryKey: ["server-config"],
    queryFn: () => systemApi.getServerConfig().then((r) => r.data),
  });

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health().then((r) => r.data),
    refetchInterval: 10_000,
  });

  const { data: metrics } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: () => systemApi.getMetrics().then((r) => r.data),
    refetchInterval: 3_000,
  });

  // Rolling history for sparklines
  const [ramHistory, setRamHistory] = useState<number[]>([]);
  const [cpuHistory, setCpuHistory] = useState<number[]>([]);
  const [diskHistory, setDiskHistory] = useState<number[]>([]);

  useEffect(() => {
    if (!metrics) return;
    setRamHistory((prev) => [...prev.slice(-19), metrics.ram_percent]);
    setCpuHistory((prev) => [...prev.slice(-19), metrics.cpu_percent]);
    setDiskHistory((prev) => [...prev.slice(-19), metrics.disk_percent]);
  }, [metrics]);

  // ── Mutations ─────────────────────────────────────────────────────────────

  const updateCfg = useMutation({
    mutationFn: (data: ServerConfigUpdate) => systemApi.updateServerConfig(normalizeServerConfigUpdate(data)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["server-config"] }),
  });

  const applyConfig = useMutation({
    mutationFn: () => systemApi.applyConfig(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["server-config"] });
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["server-config"] }),
  });

  const exportBackup = useMutation({ mutationFn: () => systemApi.exportBackup() });

  // ── Server config form ────────────────────────────────────────────────────

  const {
    register: regCfg,
    handleSubmit: handleCfgSubmit,
    setValue: setCfgValue,
    watch: watchCfg,
    formState: { isDirty: cfgDirty },
    reset: resetCfg,
  } = useForm<ServerConfigUpdate>();

  useEffect(() => {
    if (cfg)
      resetCfg({
        endpoint: cfg.endpoint,
        listen_port: cfg.listen_port,
        dns: cfg.dns ?? "",
        mtu: cfg.mtu ?? 1420,
        address: cfg.address,
        vpn_domain: cfg.vpn_domain ?? "",
        admin_port: cfg.admin_port,
        api_http_port: cfg.api_http_port,
        api_https_port: cfg.api_https_port,
        api_http_enabled: cfg.api_http_enabled,
      });
  }, [cfg, resetCfg]);

  // ── Dialog states ─────────────────────────────────────────────────────────

  const [regenKeyDialog, setRegenKeyDialog] = useState(false);
  const [rebootDialog, setRebootDialog] = useState(false);
  const [subnetDialog, setSubnetDialog] = useState<{ current: string; pending: string } | null>(null);
  const [portDialog, setPortDialog] = useState<{ pending: number } | null>(null);
  const [backupDialog, setBackupDialog] = useState(false);
  const [restoreDialog, setRestoreDialog] = useState(false);
  const [restoreFile, setRestoreFile] = useState<File | null>(null);

  const restoreBackup = useMutation({
    mutationFn: async (file: File) => {
      await systemApi.importBackup(file);
    },
    onSuccess: () => {
      setRestoreDialog(false);
      setRestoreFile(null);
      alert("Backup restored. Please restart the service.");
    },
    onError: (err) => {
      alert(`Restore failed: ${err}`);
    },
  });

  if (isLoading) return <p className="text-sm text-on-surface-variant">Loading…</p>;
  if (!cfg) return null;

  const wgUp = health?.wg_interface === "up";
  const dbOk = health?.db === "ok";

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="pb-16 space-y-6">
      {/* Tab Navigation */}
      <div className="flex border-b border-outline-variant/20">
        {[
          { id: "monitor" as const, label: "System Monitor" },
          { id: "general" as const, label: "General Settings" },
          { id: "test" as const, label: "Test" },
          { id: "ad" as const, label: "Active Directory" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "monitor" && (
        <section id="monitor">
          {/* Server Status - full width */}
          <div className="bg-surface-container rounded-xl p-5 md:p-7 border border-outline-variant/10 mb-6">
            <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
              Server Status
            </span>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mt-4">
              {/* Database */}
              <div className={cn(
                "flex flex-col items-center gap-1.5 md:gap-2 p-3 md:p-4 rounded-xl",
                dbOk ? "bg-tertiary/10" : "bg-error/10"
              )}>
                <div className={cn("w-2.5 h-2.5 md:w-3 md:h-3 rounded-full", dbOk ? "bg-tertiary animate-pulse" : "bg-error")} />
                <span className={cn("text-base md:text-lg font-bold", dbOk ? "text-tertiary" : "text-error")}>
                  {dbOk ? "OK" : "Error"}
                </span>
                <span className="text-[10px] md:text-xs text-on-surface-variant">Database</span>
              </div>

              {/* WireGuard */}
              <div className={cn(
                "flex flex-col items-center gap-1.5 md:gap-2 p-3 md:p-4 rounded-xl",
                wgUp ? "bg-tertiary/10" : "bg-error/10"
              )}>
                <div className={cn("w-2.5 h-2.5 md:w-3 md:h-3 rounded-full", wgUp ? "bg-tertiary animate-pulse" : "bg-error")} />
                <span className={cn("text-base md:text-lg font-bold", wgUp ? "text-tertiary" : "text-error")}>
                  {wgUp ? "Up" : "Down"}
                </span>
                <span className="text-[10px] md:text-xs text-on-surface-variant">WireGuard</span>
              </div>

              {/* Tunnels */}
              <div className="flex flex-col items-center gap-1.5 md:gap-2 p-3 md:p-4 rounded-xl bg-primary/10">
                <span className="text-xl md:text-2xl font-bold text-primary">{health?.tunnel_count ?? 0}</span>
                <span className="text-[10px] md:text-xs text-on-surface-variant">Tunnels</span>
              </div>

              {/* Uptime */}
              <div className="flex flex-col items-center gap-1.5 md:gap-2 p-3 md:p-4 rounded-xl bg-secondary/10">
                <span className="text-base md:text-lg font-bold text-secondary">
                  {health?.uptime_seconds ? formatUptime(health.uptime_seconds) : "—"}
                </span>
                <span className="text-[10px] md:text-xs text-on-surface-variant">Uptime</span>
              </div>
            </div>
          </div>

          {/* Resource cards - 3 equal columns */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CPU card */}
            <div className="bg-surface-container rounded-xl p-5 md:p-7 flex items-center justify-between border border-outline-variant/10 hover:bg-surface-container-high transition-colors">
              <div className="space-y-0 min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Host CPU Usage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl md:text-4xl font-extrabold text-secondary tracking-tighter">
                    {metrics ? `${metrics.cpu_percent}%` : "—"}
                  </span>
                  <span className="text-xs md:text-sm text-on-surface-variant font-medium">
                    {metrics ? `${metrics.cpu_count} Cores` : ""}
                  </span>
                </div>
                <Sparkline data={cpuHistory} colorClass="bg-secondary" />
              </div>
              <DonutGauge
                percent={metrics?.cpu_percent ?? 0}
                colorClass="text-secondary"
                icon="developer_board"
              />
            </div>

            {/* RAM card */}
            <div className="bg-surface-container rounded-xl p-5 md:p-7 flex items-center justify-between border border-outline-variant/10 hover:bg-surface-container-high transition-colors">
              <div className="space-y-0 min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Host RAM Usage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl md:text-4xl font-extrabold text-primary tracking-tighter">
                    {metrics ? `${metrics.ram_percent}%` : "—"}
                  </span>
                  <span className="text-xs md:text-sm text-on-surface-variant font-medium">
                    {metrics ? `/ ${metrics.ram_total_gb} GB` : ""}
                  </span>
                </div>
                <Sparkline data={ramHistory} colorClass="bg-primary" />
              </div>
              <DonutGauge percent={metrics?.ram_percent ?? 0} colorClass="text-primary" icon="memory" />
            </div>

            {/* Disk card */}
            <div className="bg-surface-container rounded-xl p-5 md:p-7 flex items-center justify-between border border-outline-variant/10 hover:bg-surface-container-high transition-colors">
              <div className="space-y-0 min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Host Disk Usage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl md:text-4xl font-extrabold text-tertiary tracking-tighter">
                    {metrics ? `${metrics.disk_percent}%` : "—"}
                  </span>
                  <span className="text-xs md:text-sm text-on-surface-variant font-medium">
                    {metrics ? `/ ${metrics.disk_total_gb} GB` : ""}
                  </span>
                </div>
                <Sparkline data={diskHistory} colorClass="bg-tertiary" />
              </div>
              <DonutGauge
                percent={metrics?.disk_percent ?? 0}
                colorClass="text-tertiary"
                icon="storage"
              />
            </div>
          </div>
        </section>
      )}

      {activeTab === "general" && (
        <div className="grid grid-cols-1 gap-6">
          {/* Server Config */}
          <section className="bg-surface-container rounded-xl p-8 border border-outline-variant/10">
            <header className="mb-7">
              <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                  tune
                </span>
                General Settings
              </h3>
            </header>

            <form onSubmit={handleCfgSubmit((d) => updateCfg.mutate(d))} className="space-y-6">
              {/* Server Public Key */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Server Public Key
                </label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-surface-container-high px-4 py-3 rounded-lg font-mono text-sm text-on-surface break-all">
                    {cfg?.public_key ?? "—"}
                  </code>
                  <CopyButton value={cfg?.public_key ?? ""} />
                  <button
                    type="button"
                    onClick={() => setRegenKeyDialog(true)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-outline hover:text-error transition-colors ml-1 whitespace-nowrap"
                  >
                    <KeyRound className="h-3.5 w-3.5" />
                    Regenerate
                  </button>
                </div>
                {regenerateKey.isSuccess && (
                  <p className="text-xs text-secondary font-medium mt-2 pl-1">Keypair regenerated.</p>
                )}
              </div>

              {/* Endpoint */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Endpoint (Public IP/DDNS)
                </label>
                <Input
                  {...regCfg("endpoint")}
                  placeholder="vpn.example.com or 203.0.113.1"
                  className="max-w-md"
                />
              </div>

              {/* Listen Port */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Listen Port
                </label>
                <Input
                  {...regCfg("listen_port")}
                  type="number"
                  className="max-w-32"
                />
              </div>

              {/* DNS Servers */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  DNS Servers (optional)
                </label>
                <Input
                  {...regCfg("dns")}
                  placeholder="1.1.1.1, 8.8.8.8"
                  className="max-w-md"
                />
                <p className="text-[11px] text-on-surface-variant mt-1">Comma-separated list of DNS servers for clients</p>
              </div>

              {/* MTU */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  MTU (optional)
                </label>
                <Input
                  {...regCfg("mtu")}
                  type="number"
                  placeholder="1420"
                  className="max-w-32"
                />
              </div>

              {/* Subnet */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  VPN Subnet
                </label>
                <div className="flex items-center gap-3">
                  <Input
                    {...regCfg("address")}
                    placeholder="10.169.0.1/24"
                    className="max-w-48 font-mono"
                    onChange={(e) => {
                      regCfg("address").onChange(e);
                      setSubnetDialog({ current: cfg?.address ?? "", pending: e.target.value });
                    }}
                  />
                  {subnetDialog && subnetDialog.pending !== subnetDialog.current && (
                    <button
                      type="button"
                      onClick={() => setSubnetDialog(null)}
                      className="text-xs text-error hover:underline"
                    >
                      Cancel
                    </button>
                  )}
                </div>
                <p className="text-[11px] text-on-surface-variant mt-1">Changing this disconnects all clients</p>
              </div>

              {/* VPN Domain */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  VPN Domain
                </label>
                <Input
                  {...regCfg("vpn_domain")}
                  placeholder="example.vpn"
                  className="max-w-md"
                />
                <p className="text-[11px] text-on-surface-variant mt-1">Used for future hostname implementations</p>
              </div>

              {/* Admin Port */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  Dashboard Admin Port
                </label>
                <Input
                  {...regCfg("admin_port")}
                  type="number"
                  className="max-w-32"
                />
              </div>

              {/* API HTTP Port */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  API HTTP Port
                </label>
                <Input
                  {...regCfg("api_http_port")}
                  type="number"
                  className="max-w-32"
                />
              </div>

              {/* API HTTP Enabled */}
              <div className="flex items-center gap-3">
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Enable HTTP API
                </label>
                <button
                  type="button"
                  onClick={() => setCfgValue("api_http_enabled", !watchCfg("api_http_enabled"))}
                  className={cn(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    watchCfg("api_http_enabled") ? "bg-primary" : "bg-surface-container-high"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      watchCfg("api_http_enabled") ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
              </div>

              {/* API HTTPS Port */}
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                  API HTTPS Port
                </label>
                <Input
                  {...regCfg("api_https_port")}
                  type="number"
                  className="max-w-32"
                />
              </div>

              {/* Theme Toggle */}
              <div className="flex items-center gap-4">
                <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Theme</span>
                <div className="flex bg-surface-container rounded-full p-1">
                  <button
                    type="button"
                    onClick={() => theme !== "light" && toggleTheme()}
                    className={cn(
                      "flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-all",
                      theme === "light" ? "bg-surface-container-high text-on-surface" : "text-on-surface-variant"
                    )}
                  >
                    <span
                      className="material-symbols-outlined text-base"
                      style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                    >
                      light_mode
                    </span>
                    Light
                  </button>
                  <button
                    type="button"
                    onClick={() => theme !== "dark" && toggleTheme()}
                    className={cn(
                      "flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-all",
                      theme === "dark" ? "bg-surface-container-high text-on-surface" : "text-on-surface-variant"
                    )}
                  >
                    <span
                      className="material-symbols-outlined text-base"
                      style={{
                        fontVariationSettings:
                          theme === "dark" ? "'FILL' 1, 'wght' 400" : "'FILL' 0, 'wght' 300",
                      }}
                    >
                      dark_mode
                    </span>
                    Dark
                  </button>
                </div>
              </div>

              {/* Save */}
              <div className="flex items-center gap-4 pt-2">
                <button
                  type="submit"
                  disabled={updateCfg.isPending || !cfgDirty}
                  className="bg-primary text-on-primary font-bold py-3 px-8 rounded-full shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100"
                >
                  {updateCfg.isPending ? "Saving…" : "Save Changes"}
                </button>
                {updateCfg.isSuccess && <span className="text-sm text-secondary font-medium">Saved.</span>}
                {updateCfg.isError && <span className="text-sm text-error">Error saving.</span>}
              </div>
            </form>
          </section>

          {/* Backup & Restore - full width */}
          <section className="bg-surface-container rounded-xl p-8 border border-outline-variant/10">
            <header className="mb-6">
              <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                  cloud_upload
                </span>
                Backup &amp; Restore
              </h3>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Download Backup */}
              <div className="text-center">
                <div className="bg-surface-container-high rounded-xl p-6 mb-4">
                  <span className="material-symbols-outlined text-4xl text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                    download
                  </span>
                </div>
                <h4 className="font-bold text-on-surface mb-2">Download Backup</h4>
                <p className="text-sm text-on-surface-variant mb-4">Export database and .env</p>
                <Button onClick={() => setBackupDialog(true)} variant="outline">
                  Download Backup
                </Button>
              </div>

              {/* Restore Backup */}
              <div className="text-center">
                <div className="bg-surface-container-high rounded-xl p-6 mb-4">
                  <span className="material-symbols-outlined text-4xl text-tertiary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                    upload
                  </span>
                </div>
                <h4 className="font-bold text-on-surface mb-2">Restore Backup</h4>
                <p className="text-sm text-on-surface-variant mb-4">Upload a backup file</p>
                <label className="inline-flex items-center gap-2 px-4 py-2 bg-tertiary text-white text-sm font-bold rounded-full cursor-pointer hover:opacity-90 transition-opacity">
                  <span>Choose File</span>
                  <input
                    id="restore-file"
                    type="file"
                    accept=".db"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) setRestoreFile(file);
                    }}
                  />
                </label>
                {restoreFile && (
                  <Button
                    onClick={() => setRestoreDialog(true)}
                    variant="outline"
                    className="ml-2"
                  >
                    Restore
                  </Button>
                )}
                <p className="text-[11px] text-on-surface-variant text-center mt-2">
                  Restore requires a service restart to take effect.
                </p>
              </div>
            </div>

            {/* Reboot WG */}
            <div className="mt-8 pt-6 border-t border-outline-variant/20">
              <div className="flex items-center justify-between p-4 bg-tertiary/10 rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                    warning
                  </span>
                  <div>
                    <p className="text-xs font-bold text-tertiary uppercase tracking-wide">Advanced Action</p>
                    <p className="text-[10px] text-tertiary/80 leading-tight">Disconnects all peers briefly</p>
                  </div>
                </div>
                <button
                  onClick={() => setRebootDialog(true)}
                  disabled={wgRestart.isPending}
                  className="px-4 py-2 bg-tertiary text-white text-xs font-bold rounded-full hover:opacity-90 transition-opacity disabled:opacity-60"
                >
                  {wgRestart.isPending ? "…" : "Reboot WG"}
                </button>
              </div>
              {wgRestart.isSuccess && (
                <p className="text-xs text-secondary font-medium text-center mt-2">WireGuard restarted.</p>
              )}
            </div>
          </section>

          {/* Reset Onboarding */}
          <section className="bg-surface-container rounded-xl p-8 border border-outline-variant/10">
            <header className="mb-6">
              <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>
                  refresh
                </span>
                Reset Setup Wizard
              </h3>
            </header>
            <p className="text-sm text-on-surface-variant mb-4">
              Reset the setup wizard to allow re-running the initial configuration. The user will be prompted to complete the setup again.
            </p>
            <Button
              variant="outline"
              onClick={() => {
                if (confirm("Are you sure you want to reset the setup wizard?")) {
                  systemApi.resetOnboarding().then(() => {
                    window.location.reload();
                  });
                }
              }}
            >
              Reset Onboarding
            </Button>
          </section>
        </div>
      )}

      {activeTab === "test" && (
        <SpeedTestTab />
      )}

      {activeTab === "ad" && (
        <ADConfigurationTab />
      )}

      <ConfirmDialog
        open={regenKeyDialog}
        onOpenChange={setRegenKeyDialog}
        title="Regenerate Server Keypair"
        description="This will generate a new keypair and disconnect all clients. All peer configs must be regenerated."
        onConfirm={() => regenerateKey.mutate()}
        confirmLabel="Regenerate Key"
        danger
      />

      <ConfirmDialog
        open={rebootDialog}
        onOpenChange={setRebootDialog}
        title="Reboot WireGuard"
        description="This will apply the current config, restart the WireGuard interface, and briefly disconnect all active peers."
        onConfirm={() => wgRestart.mutate()}
        confirmLabel="Reboot"
        danger
      />

      <ConfirmDialog
        open={!!subnetDialog}
        onOpenChange={(v) => !v && setSubnetDialog(null)}
        title="Change VPN Subnet"
        description={
          <>
            Changing the subnet will disconnect all connected clients. All peer configs must be
            updated.
            <br />
            <br />
            New subnet:{" "}
            <code className="font-mono text-primary">{subnetDialog?.pending}</code>
          </>
        }
        onConfirm={() => {
          if (subnetDialog) updateCfg.mutate({ address: subnetDialog.pending });
        }}
        confirmLabel="Change Subnet"
        danger
      />

      <ConfirmDialog
        open={!!portDialog}
        onOpenChange={(v) => !v && setPortDialog(null)}
        title="Change Listen Port"
        description={
          <>
            Changing the port will disconnect all connected clients. All peer configs must be
            updated.
            <br />
            <br />
            New port:{" "}
            <code className="font-mono text-primary">{portDialog?.pending}</code>
          </>
        }
        onConfirm={() => {
          if (portDialog) updateCfg.mutate({ listen_port: portDialog.pending });
        }}
        confirmLabel="Change Port"
        danger
      />

      <ConfirmDialog
        open={backupDialog}
        onOpenChange={setBackupDialog}
        title="Download Backup"
        description="This will export the database file and .env configuration as a backup."
        onConfirm={() => {
          setBackupDialog(false);
          systemApi.exportBackup();
        }}
        confirmLabel="Download"
      />

      <ConfirmDialog
        open={restoreDialog}
        onOpenChange={(v) => {
          setRestoreDialog(v);
          if (!v) setRestoreFile(null);
        }}
        title="Restore Backup"
        description={
          <>
            <span className="text-error font-bold">Warning:</span> Restoring a backup will replace all current data. 
            This action cannot be undone.
            <br /><br />
            Selected file: <code className="font-mono">{restoreFile?.name}</code>
          </>
        }
        onConfirm={() => {
          if (restoreFile) restoreBackup.mutate(restoreFile);
        }}
        confirmLabel="Restore"
        danger
      />
    </div>
  );
}
