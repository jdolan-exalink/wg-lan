import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "@/api/auth";
import type { User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

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

  const login = async (username: string, password: string): Promise<User> => {
    const res = await authApi.login(username, password);
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
