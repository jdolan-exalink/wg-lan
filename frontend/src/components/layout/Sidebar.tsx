import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Users,
  Network,
  MapPin,
  Shield,
  ShieldCheck,
  Settings,
  Database,
  Activity,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/api/system";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/peers", label: "Peers", icon: Users },
  { to: "/networks", label: "Networks", icon: Network },
  { to: "/zones", label: "Zones", icon: MapPin },
  { to: "/groups", label: "Groups", icon: Shield },
  { to: "/policies", label: "Policies", icon: ShieldCheck },
  { to: "/system", label: "System", icon: Settings },
];

export function Sidebar() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health().then((r) => r.data),
    refetchInterval: 10_000,
  });

  return (
    <aside className="flex flex-col w-56 min-h-screen border-r bg-card">
      <div className="flex items-center gap-2 h-14 px-4 border-b">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg tracking-tight">NetLoom</span>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <Separator />
      {/* Service Status */}
      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Database className="h-3 w-3" />
            <span>DB</span>
          </div>
          <Badge
            variant={health?.db === "ok" ? "default" : "destructive"}
            className="h-4 px-1.5 text-[10px] leading-none"
          >
            {health?.db ?? "—"}
          </Badge>
        </div>
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Activity className="h-3 w-3" />
            <span>WG</span>
          </div>
          <Badge
            variant={health?.wg_interface === "up" ? "default" : "secondary"}
            className="h-4 px-1.5 text-[10px] leading-none"
          >
            {health?.wg_interface ?? "—"}
          </Badge>
        </div>
      </div>
      <div className="px-4 py-2 text-xs text-muted-foreground border-t">v0.1.0</div>
    </aside>
  );
}
