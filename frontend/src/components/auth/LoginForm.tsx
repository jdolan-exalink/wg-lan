import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { versionApi } from "@/api/version";

const schema = z.object({
  username: z.string().min(1, "Username required"),
  password: z.string().min(1, "Password required"),
});

type FormData = z.infer<typeof schema>;

const AUTH_METHOD_COOKIE = "netloom_auth_method";

function getSavedAuthMethod(): string {
  if (typeof document === "undefined") return "auto";
  const match = document.cookie.match(new RegExp("(^| )" + AUTH_METHOD_COOKIE + "=([^;]+)"));
  return match ? match[2] : "auto";
}

function setSavedAuthMethod(method: string) {
  if (typeof document === "undefined") return;
  const expires = new Date();
  expires.setFullYear(expires.getFullYear() + 1);
  document.cookie = `${AUTH_METHOD_COOKIE}=${method};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
}

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [authMethod, setAuthMethod] = useState("auto");

  useEffect(() => {
    setAuthMethod(getSavedAuthMethod());
  }, []);

  const { data: version } = useQuery({
    queryKey: ["version"],
    queryFn: () => versionApi.get().then((r) => r.data),
    staleTime: Infinity,
  });

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      const user = await login(data.username, data.password, authMethod);
      setSavedAuthMethod(authMethod);
      if (user.must_change_password) {
        navigate("/change-password");
      } else {
        navigate("/");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-surface-dim relative overflow-hidden">
      {/* Background Decoration */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary-container opacity-[0.03] blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-tertiary opacity-[0.02] blur-[150px]" />
        <div
          className="absolute inset-0"
          style={{ backgroundImage: "radial-gradient(circle at 2px 2px, rgba(71, 69, 85, 0.05) 1px, transparent 0)", backgroundSize: "40px 40px" }}
        />
      </div>

      {/* Main Login Portal */}
      <div className="z-10 w-full max-w-md px-6">
        {/* Logo Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center mb-4">
            <div className="w-16 h-16 rounded-xl kinetic-gradient flex items-center justify-center shadow-lg shadow-primary-container/20">
              <span className="material-symbols-outlined text-on-primary-container filled text-4xl">hub</span>
            </div>
          </div>
          <h1 className="font-headline font-black text-4xl tracking-tighter text-on-surface">
            NETLoom VPN
          </h1>
          <p className="font-label text-xs uppercase tracking-widest text-outline mt-2">
            WireGuard®
          </p>
        </div>

        {/* Central Login Card */}
        <Card className="glass-panel kinetic-glow border border-outline-variant/15 rounded-xl p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          <CardHeader className="text-center px-0 pt-0">
            <CardTitle className="font-label text-[10px] uppercase tracking-widest text-outline-variant">
              System Access
            </CardTitle>
          </CardHeader>
          <CardContent className="px-0">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Auth Method Selector */}
              <div className="space-y-2">
                <Label className="font-label text-[10px] uppercase tracking-widest text-outline-variant block ml-1">
                  Authentication Method
                </Label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setAuthMethod("auto")}
                    className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                      authMethod === "auto"
                        ? "bg-primary-container text-on-primary-container"
                        : "bg-surface-container-lowest text-outline-variant hover:bg-surface-container-high"
                    }`}
                  >
                    Auto
                  </button>
                  <button
                    type="button"
                    onClick={() => setAuthMethod("ad")}
                    className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                      authMethod === "ad"
                        ? "bg-primary-container text-on-primary-container"
                        : "bg-surface-container-lowest text-outline-variant hover:bg-surface-container-high"
                    }`}
                  >
                    AD
                  </button>
                  <button
                    type="button"
                    onClick={() => setAuthMethod("local")}
                    className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                      authMethod === "local"
                        ? "bg-primary-container text-on-primary-container"
                        : "bg-surface-container-lowest text-outline-variant hover:bg-surface-container-high"
                    }`}
                  >
                    Local
                  </button>
                </div>
              </div>

              {/* Username Field */}
              <div className="space-y-2">
                <Label className="font-label text-[10px] uppercase tracking-widest text-outline-variant block ml-1" htmlFor="username">
                  System Identity
                </Label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-outline-variant group-focus-within:text-primary transition-colors">
                    <span className="material-symbols-outlined text-xl">account_circle</span>
                  </div>
                  <Input
                    id="username"
                    autoComplete="username"
                    placeholder="Username"
                    className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg py-3.5 pl-12 pr-4 text-sm font-body text-on-surface placeholder:text-outline-variant focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all duration-200"
                    {...register("username")}
                  />
                </div>
                {errors.username && <p className="text-xs text-destructive ml-1">{errors.username.message}</p>}
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label className="font-label text-[10px] uppercase tracking-widest text-outline-variant block ml-1" htmlFor="password">
                  Security Key
                </Label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-outline-variant group-focus-within:text-primary transition-colors">
                    <span className="material-symbols-outlined text-xl">lock</span>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg py-3.5 pl-12 pr-4 text-sm font-body text-on-surface placeholder:text-outline-variant focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all duration-200"
                    {...register("password")}
                  />
                </div>
                {errors.password && <p className="text-xs text-destructive ml-1">{errors.password.message}</p>}
              </div>

              {error && (
                <div className="rounded-md bg-error-container/10 border border-error/10 px-4 py-3 text-sm text-error">
                  {error}
                </div>
              )}

              {/* Sign In Button */}
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 px-6 rounded-lg bg-primary-container text-on-primary-container font-headline font-bold text-sm tracking-tight transition-all duration-200 hover:scale-[1.01] active:scale-[0.98] inner-glow flex items-center justify-center gap-2 group"
              >
                Login
              </Button>
            </form>

            {/* Bottom Action */}
            <div className="mt-8 pt-6 border-t border-outline-variant/10 text-center">
              <p className="text-sm text-outline font-body">
                DOLAN SS 2026 - V{version ? version.version : "0.7.1"}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Auxiliary Links */}
        <div className="mt-8 flex justify-center gap-8">
          <div className="flex items-center gap-2 text-outline-variant hover:text-outline transition-colors cursor-pointer">
            <span className="material-symbols-outlined text-lg">shield</span>
            <span className="font-label text-[10px] uppercase tracking-widest">Global Security</span>
          </div>
          <div className="flex items-center gap-2 text-outline-variant hover:text-outline transition-colors cursor-pointer">
            <span className="material-symbols-outlined text-lg">language</span>
            <span className="font-label text-[10px] uppercase tracking-widest">Network Status</span>
          </div>
        </div>
      </div>

      {/* Minimalist Footer */}
      <footer className="absolute bottom-8 w-full px-8 flex flex-col md:flex-row justify-between items-center opacity-40">
        <div className="flex items-center gap-4 mb-4 md:mb-0">
          <p className="font-label text-[10px] uppercase tracking-widest text-outline">
            © 2026 NetLoom Systems
          </p>
          <div className="w-1 h-1 rounded-full bg-outline-variant" />
          <p className="font-label text-[10px] uppercase tracking-widest text-outline">
            All Rights Reserved
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-surface-container-high border border-outline-variant/10">
            <div className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse shadow-[0_0_8px_rgba(0,218,243,0.6)]" />
            <span className="font-label text-[10px] uppercase tracking-widest text-tertiary">System Online</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
