import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "@/api/auth";
import type { User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string, authMethod?: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const AUTH_METHOD_COOKIE = "netloom_auth_method";

function getAuthMethodFromCookie(): string {
  if (typeof document === "undefined") return "auto";
  const match = document.cookie.match(new RegExp("(^| )" + AUTH_METHOD_COOKIE + "=([^;]+)"));
  return match ? match[2] : "auto";
}

function setAuthMethodCookie(method: string) {
  if (typeof document === "undefined") return;
  const expires = new Date();
  expires.setFullYear(expires.getFullYear() + 1);
  document.cookie = `${AUTH_METHOD_COOKIE}=${method};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = async () => {
    try {
      const res = await authApi.me();
      setUser(res.data);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    refresh().finally(() => setIsLoading(false));
  }, []);

  const login = async (username: string, password: string, authMethod?: string): Promise<User> => {
    const method = authMethod || getAuthMethodFromCookie();
    const res = await authApi.login(username, password, method);
    setAuthMethodCookie(method);
    setUser(res.data);
    return res.data;
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
