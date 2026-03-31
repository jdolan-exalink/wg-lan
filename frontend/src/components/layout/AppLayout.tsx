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
};

export function AppLayout() {
  const { pathname } = useLocation();
  const title = pageTitles[pathname] ?? "WG-LAN";

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
