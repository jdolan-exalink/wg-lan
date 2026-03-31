import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/api/system";
import { versionApi } from "@/api/version";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/peers", label: "Peers", icon: "hub" },
  { to: "/networks", label: "Networks", icon: "lan" },
  { to: "/zones", label: "Zones", icon: "security" },
  { to: "/groups", label: "Groups", icon: "group" },
  { to: "/policies", label: "Policies", icon: "policy" },
  { to: "/logs", label: "Logs", icon: "receipt_long" },
  { to: "/system", label: "System", icon: "settings" },
];

export function Sidebar() {
  const { user } = useAuth();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health().then((r) => r.data),
    refetchInterval: 10_000,
  });

  const { data: version } = useQuery({
    queryKey: ["version"],
    queryFn: () => versionApi.get().then((r) => r.data),
    staleTime: Infinity,
  });

  return (
    <aside className="fixed left-0 top-0 h-full flex flex-col py-6 bg-surface-container w-64 z-50">
      {/* Logo */}
      <div className="px-6 mb-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg kinetic-gradient flex items-center justify-center shadow-lg shadow-primary-container/20">
            <span className="material-symbols-outlined text-on-primary-container filled text-2xl">hub</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tighter text-on-surface font-headline">NetLoom</h1>
            <p className="font-label text-[10px] uppercase tracking-widest text-outline">
              {version ? `v${version.version}` : "Loading..."}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navItems.map(({ to, label, icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-all duration-300 rounded-lg group",
                isActive
                  ? "bg-surface-container-high text-tertiary shadow-sm shadow-black/20"
                  : "text-outline hover:text-on-surface hover:bg-surface-container-high/50"
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className="material-symbols-outlined text-xl"
                  style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                >
                  {icon}
                </span>
                <span className="font-label text-xs tracking-tight">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Service Status */}
      <div className="px-4 pb-2">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-container-high/40">
          <div className={cn(
            "w-2 h-2 rounded-full",
            health?.db === "ok" ? "bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]" : "bg-error"
          )} />
          <span className="font-label text-[10px] uppercase tracking-widest text-outline">DB: {health?.db ?? "—"}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-container-high/40 mt-1">
          <div className={cn(
            "w-2 h-2 rounded-full",
            health?.wg_interface === "up" ? "bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]" : "bg-outline"
          )} />
          <span className="font-label text-[10px] uppercase tracking-widest text-outline">WG: {health?.wg_interface ?? "—"}</span>
        </div>
      </div>

      <Separator className="my-2 bg-outline-variant/10" />

      {/* User */}
      <div className="px-6">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-surface-container-low/50">
          <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-xs font-bold text-on-primary-container">
            {user?.username?.charAt(0).toUpperCase() ?? "A"}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-xs font-semibold truncate font-headline">{user?.username ?? "Admin"}</p>
            <p className="text-[10px] text-outline truncate font-label uppercase">
              {user?.is_admin ? "Root Node" : "User"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
