import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginForm } from "@/components/auth/LoginForm";
import { ChangePasswordForm } from "@/components/auth/ChangePasswordForm";
import { OnboardingWizard } from "@/components/auth/OnboardingWizard";
import { DashboardPage } from "@/pages/DashboardPage";
import { PeersPage } from "@/pages/PeersPage";
import { NetworksPage } from "@/pages/NetworksPage";
import { GroupsPage } from "@/pages/GroupsPage";
import { PoliciesPage } from "@/pages/PoliciesPage";
import { SystemPage } from "@/pages/SystemPage";
import { LogsPage } from "@/pages/LogsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  if (isLoading) return <div className="flex h-screen items-center justify-center text-muted-foreground">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.must_change_password) return <Navigate to="/change-password" replace />;
  if (!user?.onboarding_completed) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/change-password" element={<ChangePasswordForm />} />
            <Route path="/onboarding" element={<OnboardingWizard />} />
            <Route
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/peers" element={<PeersPage />} />
              <Route path="/networks" element={<NetworksPage />} />
              <Route path="/groups" element={<GroupsPage />} />
              <Route path="/policies" element={<PoliciesPage />} />
              <Route path="/system" element={<SystemPage />} />
              <Route path="/logs" element={<LogsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
