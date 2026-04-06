import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginForm } from "@/components/auth/LoginForm";
import { ChangePasswordForm } from "@/components/auth/ChangePasswordForm";
import { OnboardingWizard } from "@/components/auth/OnboardingWizard";
import { IpGroupsPage } from "@/pages/IpGroupsPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { PeersPage } from "@/pages/PeersPage";
import { NetworksPage } from "@/pages/NetworksPage";
import { UsersPage } from "@/pages/UsersPage";
import { GroupsPage } from "@/pages/GroupsPage";
import { PoliciesPage } from "@/pages/PoliciesPage";
import { SystemPage } from "@/pages/SystemPage";
import { LogsPage } from "@/pages/LogsPage";
import { systemApi } from "@/api/system";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health().then((r) => r.data),
    retry: false,
    staleTime: Infinity,
    enabled: isAuthenticated,
  });

  if (isLoading) return <div className="flex h-screen items-center justify-center text-muted-foreground">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.must_change_password) return <Navigate to="/change-password" replace />;
  
  const isSystemReady = health?.is_initialized ?? true;
  if (!isSystemReady) {
    return <Navigate to="/onboarding" replace />;
  }
  
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
              <Route path="/ip-groups" element={<IpGroupsPage />} />
              <Route path="/users" element={<UsersPage />} />
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
