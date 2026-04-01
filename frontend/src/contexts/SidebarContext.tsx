import { createContext, useContext, useState } from "react";

interface SidebarCtx {
  collapsed: boolean;
  toggle: () => void;
}

const SidebarContext = createContext<SidebarCtx | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("netloom-sidebar") === "collapsed";
  });

  const toggle = () => {
    setCollapsed((v) => {
      const next = !v;
      localStorage.setItem("netloom-sidebar", next ? "collapsed" : "expanded");
      return next;
    });
  };

  return (
    <SidebarContext.Provider value={{ collapsed, toggle }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used inside SidebarProvider");
  return ctx;
}
