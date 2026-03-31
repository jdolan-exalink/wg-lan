import { useAuth } from "@/contexts/AuthContext";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-40 flex justify-between items-center h-16 px-8 bg-surface-dim/80 backdrop-blur-xl transition-all duration-300">
      <div className="flex items-center gap-4">
        <h2 className="font-headline font-bold text-lg text-on-surface">{title}</h2>
        <div className="h-4 w-px bg-outline-variant/30" />
        <p className="font-label text-xs text-tertiary">NODE-01</p>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-outline hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined text-xl">logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
