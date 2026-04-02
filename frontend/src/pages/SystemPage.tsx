import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { systemApi, type ServerConfigUpdate } from "@/api/system";
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
import { Copy, Check, KeyRound } from "lucide-react";

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

// ─── Main component ───────────────────────────────────────────────────────────

export function SystemPage() {
  const qc = useQueryClient();
  const { theme, toggleTheme } = useTheme();

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

  useEffect(() => {
    if (!metrics) return;
    setRamHistory((prev) => [...prev.slice(-19), metrics.ram_percent]);
    setCpuHistory((prev) => [...prev.slice(-19), metrics.cpu_percent]);
  }, [metrics]);

  // ── Mutations ─────────────────────────────────────────────────────────────

  const updateCfg = useMutation({
    mutationFn: (data: ServerConfigUpdate) => systemApi.updateServerConfig(data),
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
    formState: { isDirty: cfgDirty },
    reset: resetCfg,
  } = useForm<ServerConfigUpdate>();

  useEffect(() => {
    if (cfg)
      resetCfg({
        endpoint: cfg.endpoint,
        dns: cfg.dns ?? "",
        mtu: cfg.mtu ?? 1420,
      });
  }, [cfg, resetCfg]);

  // ── Dialog states ─────────────────────────────────────────────────────────

  const [regenKeyDialog, setRegenKeyDialog] = useState(false);
  const [rebootDialog, setRebootDialog] = useState(false);
  const [subnetDialog, setSubnetDialog] = useState<{ pending: string } | null>(null);
  const [portDialog, setPortDialog] = useState<{ pending: number } | null>(null);

  if (isLoading) return <p className="text-sm text-on-surface-variant">Loading…</p>;
  if (!cfg) return null;

  const wgUp = health?.wg_interface === "up";
  const dbOk = health?.db === "ok";

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="pb-16 space-y-12">

        {/* ══ Section 1: Resource Monitor ══════════════════════════════════════ */}
        <section id="monitor">
          <header className="mb-6">
            <h2 className="text-2xl font-bold text-on-surface tracking-tight">System Resource Monitor</h2>
            <p className="text-on-surface-variant text-sm mt-1">
              Real-time performance metrics of the loom infrastructure.
            </p>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* RAM card */}
            <div className="bg-surface-container rounded-xl p-7 flex items-center justify-between border border-outline-variant/10 hover:bg-surface-container-high transition-colors">
              <div className="space-y-0 min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Host RAM Usage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-4xl font-extrabold text-primary tracking-tighter">
                    {metrics ? `${metrics.ram_percent}%` : "—"}
                  </span>
                  <span className="text-sm text-on-surface-variant font-medium">
                    {metrics ? `/ ${metrics.ram_total_gb} GB` : ""}
                  </span>
                </div>
                <Sparkline data={ramHistory} colorClass="bg-primary" />
              </div>
              <DonutGauge percent={metrics?.ram_percent ?? 0} colorClass="text-primary" icon="memory" />
            </div>

            {/* CPU card */}
            <div className="bg-surface-container rounded-xl p-7 flex items-center justify-between border border-outline-variant/10 hover:bg-surface-container-high transition-colors">
              <div className="space-y-0 min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Host CPU Usage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-4xl font-extrabold text-secondary tracking-tighter">
                    {metrics ? `${metrics.cpu_percent}%` : "—"}
                  </span>
                  <span className="text-sm text-on-surface-variant font-medium">
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
          </div>

          {/* Status + quick actions row */}
          <div className="flex flex-wrap gap-3">
            <div
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium",
                dbOk ? "bg-secondary/10 text-secondary" : "bg-error/10 text-error"
              )}
            >
              <div className={cn("w-2 h-2 rounded-full", dbOk ? "bg-secondary animate-pulse" : "bg-error")} />
              Database {dbOk ? "OK" : "Error"}
            </div>
            <div
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium",
                wgUp ? "bg-secondary/10 text-secondary" : "bg-outline/10 text-outline"
              )}
            >
              <div className={cn("w-2 h-2 rounded-full", wgUp ? "bg-secondary animate-pulse" : "bg-outline")} />
              WireGuard {wgUp ? "Up" : "Down"}
            </div>
            <button
              onClick={() => applyConfig.mutate()}
              disabled={applyConfig.isPending}
              className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-60"
            >
              <span
                className="material-symbols-outlined text-base"
                style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
              >
                sync
              </span>
              {applyConfig.isPending ? "Applying…" : "Apply Config"}
            </button>
            {applyConfig.isSuccess && (
              <span className="text-sm text-secondary font-medium self-center">Applied.</span>
            )}
          </div>
        </section>

        {/* ══ Two-column grid ═══════════════════════════════════════════════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left column — Security + General */}
          <div className="lg:col-span-2 space-y-8">

            {/* ── Section 2: Admin Password ─────────────────────────────────── */}
            <section
              id="security"
              className="bg-surface-container rounded-xl p-8 border border-outline-variant/10"
            >
              <header className="mb-7">
                <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                  <span
                    className="material-symbols-outlined text-primary"
                    style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  >
                    lock
                  </span>
                  Admin Password
                </h3>
              </header>

              <PasswordChangeForm />

              {/* Server public key */}
              <div className="mt-8 pt-8 border-t border-surface-container">
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2 pl-1">
                  Server Public Key
                </p>
                <div className="flex items-center gap-2 bg-surface rounded-lg px-4 py-3">
                  <p className="font-mono text-sm break-all flex-1 text-on-surface">{cfg.public_key}</p>
                  <CopyButton value={cfg.public_key} />
                  <button
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
            </section>

            {/* ── Section 3: General Settings ──────────────────────────────── */}
            <section
              id="general"
              className="bg-surface-container rounded-xl p-8 border border-outline-variant/10"
            >
              <header className="mb-7">
                <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                  <span
                    className="material-symbols-outlined text-primary"
                    style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  >
                    tune
                  </span>
                  General Settings
                </h3>
              </header>

              <form onSubmit={handleCfgSubmit((d) => updateCfg.mutate(d))} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                  {/* Endpoint */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1">
                      Public Endpoint
                    </label>
                    <Input
                      placeholder="vpn.example.com"
                      className="h-12 bg-surface border-none font-mono text-primary font-bold focus-visible:ring-primary"
                      {...regCfg("endpoint")}
                    />
                    <p className="text-[11px] text-on-surface-variant pl-1">
                      Hostname or IP peers use to connect
                    </p>
                  </div>

                  {/* DNS */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1">
                      DNS
                    </label>
                    <Input
                      placeholder="1.1.1.1, 8.8.8.8"
                      className="h-12 bg-surface border-none focus-visible:ring-primary"
                      {...regCfg("dns")}
                    />
                  </div>

                  {/* MTU */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1">
                      MTU
                    </label>
                    <Input
                      type="number"
                      placeholder="1420"
                      className="h-12 bg-surface border-none focus-visible:ring-primary"
                      {...regCfg("mtu", { valueAsNumber: true })}
                    />
                  </div>

                  {/* VPN Subnet (read+prompt edit) */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1">
                      VPN Subnet
                    </label>
                    <div className="flex items-center gap-2 h-12 bg-surface rounded-lg px-4">
                      <span className="font-mono text-sm text-on-surface flex-1">{cfg.address}</span>
                      <button
                        type="button"
                        className="text-xs font-semibold text-outline hover:text-primary transition-colors"
                        onClick={() => {
                          const v = prompt("New VPN Subnet (e.g. 100.169.0.1/16):", cfg.address);
                          if (v && v !== cfg.address) setSubnetDialog({ pending: v });
                        }}
                      >
                        Edit
                      </button>
                    </div>
                  </div>

                  {/* Listen Port (read+prompt edit) */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1">
                      Listen Port
                    </label>
                    <div className="flex items-center gap-2 h-12 bg-surface rounded-lg px-4">
                      <span className="font-mono text-sm text-on-surface flex-1">
                        {cfg.listen_port}/udp
                      </span>
                      <button
                        type="button"
                        className="text-xs font-semibold text-outline hover:text-primary transition-colors"
                        onClick={() => {
                          const v = prompt(
                            "New listen port (1–65535):",
                            String(cfg.listen_port)
                          );
                          if (v) {
                            const p = parseInt(v, 10);
                            if (
                              !isNaN(p) &&
                              p >= 1 &&
                              p <= 65535 &&
                              p !== cfg.listen_port
                            )
                              setPortDialog({ pending: p });
                          }
                        }}
                      >
                        Edit
                      </button>
                    </div>
                  </div>

                </div>

                {/* Theme toggle */}
                <div className="space-y-2 pt-2">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant pl-1 block">
                    UI Theme
                  </label>
                  <div className="flex bg-surface p-1 rounded-xl gap-1 max-w-xs">
                    <button
                      type="button"
                      onClick={() => theme === "dark" && toggleTheme()}
                      className={cn(
                        "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all",
                        theme === "light"
                          ? "bg-white shadow-sm text-primary"
                          : "text-on-surface-variant hover:bg-white/30"
                      )}
                    >
                      <span
                        className="material-symbols-outlined text-base"
                        style={{
                          fontVariationSettings:
                            theme === "light"
                              ? "'FILL' 1, 'wght' 400"
                              : "'FILL' 0, 'wght' 300",
                        }}
                      >
                        light_mode
                      </span>
                      Light
                    </button>
                    <button
                      type="button"
                      onClick={() => theme === "light" && toggleTheme()}
                      className={cn(
                        "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all",
                        theme === "dark"
                          ? "bg-on-surface/90 shadow-sm text-primary-container"
                          : "text-on-surface-variant hover:bg-white/30"
                      )}
                    >
                      <span
                        className="material-symbols-outlined text-base"
                        style={{
                          fontVariationSettings:
                            theme === "dark"
                              ? "'FILL' 1, 'wght' 400"
                              : "'FILL' 0, 'wght' 300",
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
                  {updateCfg.isSuccess && (
                    <span className="text-sm text-secondary font-medium">Saved.</span>
                  )}
                  {updateCfg.isError && (
                    <span className="text-sm text-error">Error saving.</span>
                  )}
                </div>
              </form>
            </section>
          </div>

          {/* ── Right column: Backup & Restore ───────────────────────────── */}
          <aside
            id="backup"
            className="bg-surface-container rounded-xl p-8 border border-outline-variant/10 flex flex-col"
          >
            <header className="mb-6">
              <h3 className="text-xl font-bold text-on-surface flex items-center gap-2">
                <span
                  className="material-symbols-outlined text-primary"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                >
                  cloud_upload
                </span>
                Backup &amp; Restore
              </h3>
            </header>

            <div className="space-y-7 flex-1">
              {/* Export backup */}
              <div className="p-5 bg-surface-container-low rounded-xl space-y-3">
                <div>
                  <h4 className="text-sm font-bold text-on-surface">System Backup</h4>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    Downloads the full database with all configurations.
                  </p>
                </div>
                <button
                  onClick={() => exportBackup.mutate()}
                  disabled={exportBackup.isPending}
                  className="w-full py-3 bg-white dark:bg-surface-container border border-primary/20 text-primary text-sm font-bold rounded-lg hover:bg-primary hover:text-white dark:hover:bg-primary transition-all flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  <span
                    className="material-symbols-outlined text-base"
                    style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  >
                    download
                  </span>
                  {exportBackup.isPending ? "Preparing…" : "Generate Full Backup"}
                </button>
                {exportBackup.isSuccess && (
                  <p className="text-xs text-secondary font-medium text-center">Download started.</p>
                )}
              </div>

              {/* Restore */}
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-bold text-on-surface">Restore System</h4>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    Roll back to a previous configuration state.
                  </p>
                </div>
                <label
                  htmlFor="restore-file"
                  className="border-2 border-dashed border-outline-variant/30 rounded-xl p-7 flex flex-col items-center justify-center text-center gap-3 group hover:border-primary transition-colors cursor-pointer"
                >
                  <div className="w-12 h-12 bg-surface-container rounded-full flex items-center justify-center text-on-surface-variant group-hover:text-primary transition-colors">
                    <span
                      className="material-symbols-outlined text-3xl"
                      style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                    >
                      upload_file
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-on-surface">Drop backup file</p>
                    <p className="text-xs text-on-surface-variant">or click to browse — .db files only</p>
                  </div>
                  <input id="restore-file" type="file" accept=".db" className="hidden" onChange={() => {}} />
                </label>
                <p className="text-[11px] text-on-surface-variant text-center">
                  Restore requires a service restart to take effect.
                </p>
              </div>
            </div>

            {/* Reboot WG */}
            <div className="mt-8 pt-6 border-t border-surface-container">
              <div className="flex items-center justify-between p-4 bg-tertiary/10 rounded-xl">
                <div className="flex items-center gap-3">
                  <span
                    className="material-symbols-outlined text-tertiary"
                    style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  >
                    warning
                  </span>
                  <div>
                    <p className="text-xs font-bold text-tertiary uppercase tracking-wide">
                      Advanced Action
                    </p>
                    <p className="text-[10px] text-tertiary/80 leading-tight">
                      Disconnects all peers briefly
                    </p>
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
                <p className="text-xs text-secondary font-medium text-center mt-2">
                  WireGuard restarted.
                </p>
              )}
            </div>
          </aside>
        </div>

      {/* ── Confirmation dialogs ─────────────────────────────────────────────── */}

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
    </div>
  );
}
