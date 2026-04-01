import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import { cn } from "@/lib/utils";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/peers": "Peers",
  "/networks": "Networks",
  "/zones": "Zones",
  "/groups": "Groups",
  "/policies": "Policies",
  "/system": "System",
  "/logs": "Logs",
};

function AppLayoutInner() {
  const { pathname } = useLocation();
  const { collapsed } = useSidebar();
  const title = pageTitles[pathname] ?? "NetLoom";

  return (
    <div className="min-h-screen bg-surface-dim">
      <Sidebar />
      <div
        className={cn(
          "content-transition min-h-screen flex flex-col",
          collapsed ? "ml-16" : "ml-64"
        )}
      >
        <Header title={title} />
        <main className="flex-1 pt-20 px-6 pb-12 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function AppLayout() {
  return (
    <SidebarProvider>
      <AppLayoutInner />
    </SidebarProvider>
  );
}
