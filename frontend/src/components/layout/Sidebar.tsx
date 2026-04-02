import { NavLink, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/api/system";
import { versionApi } from "@/api/version";
import { useAuth } from "@/contexts/AuthContext";
import { useSidebar } from "@/contexts/SidebarContext";
import { useTheme } from "@/contexts/ThemeContext";
import {
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  LogOut,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/peers", label: "Peers", icon: "hub" },
  { to: "/networks", label: "Networks", icon: "lan" },
  { to: "/users", label: "Usuarios", icon: "people" },
  { to: "/groups", label: "Groups", icon: "group" },
  { to: "/policies", label: "Policies", icon: "policy" },
  { to: "/logs", label: "Logs", icon: "receipt_long" },
  { to: "/system", label: "System", icon: "settings" },
];

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div
      className={cn(
        "w-2 h-2 rounded-full flex-shrink-0 transition-colors",
        ok ? "bg-tertiary" : "bg-error"
      )}
      title={label}
    />
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { collapsed, toggle } = useSidebar();
  const navigate = useNavigate();

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

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-full flex flex-col",
        "bg-surface-container border-r border-outline-variant/20 z-50",
        "sidebar-transition overflow-hidden",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* ── Logo bar ── */}
      <div
        className={cn(
          "relative flex items-center h-14 border-b border-outline-variant/10 flex-shrink-0",
          collapsed ? "justify-center px-0" : "px-4 gap-3"
        )}
      >
        {/* Logo mark */}
        <div className="w-8 h-8 rounded-lg kinetic-gradient flex items-center justify-center shadow-md flex-shrink-0">
          <span className="material-symbols-outlined text-white filled"
            style={{ fontSize: 18, fontVariationSettings: "'FILL' 1, 'wght' 500" }}>
            hub
          </span>
        </div>

        {/* Wordmark (hidden when collapsed) */}
        {!collapsed && (
          <div className="flex-1 overflow-hidden">
            <h1 className="text-sm font-bold tracking-tight text-on-surface font-headline leading-none">
              NetLoom
            </h1>
            <p className="font-label text-[9px] uppercase tracking-widest text-outline mt-0.5">
              {version ? `v${version.version}` : "—"}
            </p>
          </div>
        )}

        {/* Collapse toggle */}
        <button
          onClick={toggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "p-1 rounded-md text-outline hover:text-on-surface hover:bg-surface-container-high/50 transition-colors",
            collapsed
              ? "absolute -right-3 top-1/2 -translate-y-1/2 bg-surface-container border border-outline-variant/25 shadow-sm z-10"
              : "ml-auto flex-shrink-0"
          )}
        >
          {collapsed
            ? <ChevronRight className="w-3.5 h-3.5" />
            : <ChevronLeft className="w-3.5 h-3.5" />
          }
        </button>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3">
        <div className={cn("space-y-0.5", collapsed ? "px-2" : "px-3")}>
          {navItems.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center rounded-lg transition-all duration-150 group",
                  collapsed
                    ? "px-2 py-2.5 justify-center"
                    : "px-3 py-2.5 gap-3",
                  isActive
                    ? "bg-primary-container/10 text-primary"
                    : "text-outline hover:text-on-surface hover:bg-surface-container-high/40"
                )
              }
            >
              {({ isActive }) => (
                <>
                  {/* Active left bar */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-primary-container rounded-r" />
                  )}

                  <span
                    className="material-symbols-outlined flex-shrink-0"
                    style={{
                      fontSize: collapsed ? 22 : 20,
                      fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                    }}
                  >
                    {icon}
                  </span>

                  {!collapsed && (
                    <span className="font-label text-[13px] tracking-tight">{label}</span>
                  )}

                  {/* Tooltip when collapsed */}
                  {collapsed && (
                    <span className="pointer-events-none absolute left-full ml-3 px-2.5 py-1.5 rounded-lg bg-surface-container-highest text-on-surface text-xs font-label shadow-lg border border-outline-variant/20 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50">
                      {label}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* ── Service status ── */}
      <div className={cn("flex-shrink-0 pb-2", collapsed ? "px-3" : "px-4")}>
        {collapsed ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <StatusDot ok={health?.db === "ok"} label={`DB: ${health?.db ?? "?"}`} />
            <StatusDot ok={health?.wg_interface === "up"} label={`WG: ${health?.wg_interface ?? "?"}`} />
          </div>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg">
              <StatusDot ok={health?.db === "ok"} label="Database" />
              <span className="font-label text-[10px] uppercase tracking-widest text-outline">
                DB&thinsp;·&thinsp;
                <span className="text-on-surface-variant normal-case">{health?.db ?? "—"}</span>
              </span>
            </div>
            <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg">
              <StatusDot ok={health?.wg_interface === "up"} label="WireGuard" />
              <span className="font-label text-[10px] uppercase tracking-widest text-outline">
                WG&thinsp;·&thinsp;
                <span className="text-on-surface-variant normal-case">{health?.wg_interface ?? "—"}</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* ── Divider ── */}
      <div className="mx-3 h-px bg-outline-variant/20 flex-shrink-0" />

      {/* ── User section ── */}
      <div className={cn("flex-shrink-0 p-3", collapsed && "p-2")}>
        <div
          className={cn(
            "flex items-center rounded-xl bg-surface-container-high/30 border border-outline-variant/10",
            collapsed ? "p-2 flex-col gap-2 justify-center" : "p-2 gap-2"
          )}
        >
          {/* Avatar */}
          <div className="w-7 h-7 rounded-lg bg-primary-container flex items-center justify-center text-[11px] font-bold text-on-primary-container flex-shrink-0">
            {user?.username?.charAt(0).toUpperCase() ?? "A"}
          </div>

          {/* Name + role */}
          {!collapsed && (
            <div className="flex-1 overflow-hidden min-w-0">
              <p className="text-[13px] font-semibold truncate font-headline text-on-surface leading-none">
                {user?.username ?? "Admin"}
              </p>
              <p className="font-label text-[9px] uppercase tracking-widest text-outline mt-0.5">
                {user?.is_admin ? "Admin" : "User"}
              </p>
            </div>
          )}

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            title={theme === "dark" ? "Light mode" : "Dark mode"}
            className="p-1.5 rounded-md text-outline hover:text-on-surface hover:bg-surface-container-high transition-colors flex-shrink-0"
          >
            {theme === "dark"
              ? <Sun className="w-3.5 h-3.5" />
              : <Moon className="w-3.5 h-3.5" />
            }
          </button>

          {/* Logout */}
          <button
            onClick={handleLogout}
            title="Logout"
            className="p-1.5 rounded-md text-outline hover:text-error hover:bg-error-container/20 transition-colors flex-shrink-0"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
