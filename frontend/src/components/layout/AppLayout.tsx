import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/peers": "Peers",
  "/networks": "Networks",
  "/zones": "Zones",
  "/groups": "Groups",
  "/policies": "Policies",
  "/system": "System",
};

export function AppLayout() {
  const { pathname } = useLocation();
  const title = pageTitles[pathname] ?? "NetLoom";

  return (
    <div className="min-h-screen bg-surface-dim">
      <Sidebar />
      <div className="ml-64">
        <Header title={title} />
        <main className="pt-24 px-8 pb-16 min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
