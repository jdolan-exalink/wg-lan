import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Users,
  Network,
  MapPin,
  Shield,
  ShieldCheck,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/peers", label: "Peers", icon: Users },
  { to: "/networks", label: "Networks", icon: Network },
  { to: "/zones", label: "Zones", icon: MapPin },
  { to: "/groups", label: "Groups", icon: Shield },
  { to: "/policies", label: "Policies", icon: ShieldCheck },
];

export function Sidebar() {
  return (
    <aside className="flex flex-col w-56 min-h-screen border-r bg-card">
      <div className="flex items-center gap-2 h-14 px-4 border-b">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg tracking-tight">WG-LAN</span>
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
      <div className="px-4 py-3 text-xs text-muted-foreground">v0.1.0</div>
    </aside>
  );
}
