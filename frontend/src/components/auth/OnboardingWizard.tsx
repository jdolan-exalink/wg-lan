import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import client from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Rocket, ArrowRight, CheckCircle2, Info, Shield, Network, Globe } from "lucide-react";

const schema = z.object({
  server_lan_cidr: z.string().regex(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/, "Must be a valid CIDR (e.g., 192.168.1.0/24)"),
  server_lan_name: z.string().min(1, "Required").default("LAN Server"),
});

type FormData = z.infer<typeof schema>;

type Step = "welcome" | "configure" | "creating" | "done";

export function OnboardingWizard() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("welcome");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      server_lan_name: "LAN Server",
    },
  });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setStep("creating");
    try {
      const res = await client.post("/onboarding/complete", data);
      setResult(res.data);
      await refresh();
      setStep("done");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to complete onboarding");
      setStep("configure");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-lg">
        {step === "welcome" && (
          <>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-2">
                <Rocket className="h-10 w-10 text-primary" />
              </div>
              <CardTitle>Welcome to NetLoom</CardTitle>
              <CardDescription>Let's set up your WireGuard network in 3 simple steps</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0">1</div>
                  <div>
                    <p className="font-medium">Define your server's LAN</p>
                    <p className="text-sm text-muted-foreground">Tell us the local network behind the server (e.g., 192.168.1.0/24)</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0">2</div>
                  <div>
                    <p className="font-medium">We create the "All" group</p>
                    <p className="text-sm text-muted-foreground">All new peers start here with full access to everything</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0">3</div>
                  <div>
                    <p className="font-medium">Restrict via Groups later</p>
                    <p className="text-sm text-muted-foreground">Remove peers from "All" and add to specific groups to limit access</p>
                  </div>
                </div>
              </div>

              <div className="rounded-md bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 px-4 py-3 text-sm text-blue-800 dark:text-blue-200">
                <Info className="h-4 w-4 inline mr-1" />
                <strong>How it works:</strong> By default, all peers can reach all networks. To restrict a peer, remove it from the "All" group and add it to a specific group with limited policies.
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={() => setStep("configure")}>
                Get Started <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardFooter>
          </>
        )}

        {step === "configure" && (
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardHeader>
              <div className="flex justify-center mb-2">
                <Network className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Configure Server LAN</CardTitle>
              <CardDescription>Enter the CIDR of the local network where the server is deployed</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <Label>Zone Name</Label>
                <Input {...register("server_lan_name")} placeholder="LAN Server" />
                {errors.server_lan_name && <p className="text-xs text-destructive">{errors.server_lan_name.message}</p>}
              </div>
              <div className="space-y-1">
                <Label>Server LAN CIDR</Label>
                <Input {...register("server_lan_cidr")} placeholder="192.168.1.0/24" />
                {errors.server_lan_cidr && <p className="text-xs text-destructive">{errors.server_lan_cidr.message}</p>}
                <p className="text-xs text-muted-foreground">This is the network that peers will be able to reach through the VPN</p>
              </div>

              <div className="rounded-md bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
                <Shield className="h-4 w-4 inline mr-1" />
                <strong>Default: Allow All</strong> — All peers will have access to this network. You can restrict access later using Groups and Policies.
              </div>
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep("welcome")}>Back</Button>
              <Button type="submit" className="flex-1" disabled={isSubmitting}>
                {isSubmitting ? "Setting up..." : "Complete Setup"}
              </Button>
            </CardFooter>
            {error && (
              <div className="px-6 pb-4">
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
              </div>
            )}
          </form>
        )}

        {step === "creating" && (
          <>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-2">
                <div className="h-10 w-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
              </div>
              <CardTitle>Setting up your network...</CardTitle>
              <CardDescription>Creating zones, groups, and policies</CardDescription>
            </CardHeader>
          </>
        )}

        {step === "done" && (
          <>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-2">
                <CheckCircle2 className="h-10 w-10 text-green-500" />
              </div>
              <CardTitle>Setup Complete!</CardTitle>
              <CardDescription>Your WireGuard network is ready</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg bg-muted p-3">
                  <Globe className="h-5 w-5 mx-auto mb-1 text-primary" />
                  <p className="text-xs text-muted-foreground">Zone</p>
                  <p className="font-mono text-sm font-medium">{result?.zone_id}</p>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <Shield className="h-5 w-5 mx-auto mb-1 text-primary" />
                  <p className="text-xs text-muted-foreground">Group</p>
                  <p className="font-mono text-sm font-medium">{result?.group_id}</p>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <Network className="h-5 w-5 mx-auto mb-1 text-primary" />
                  <p className="text-xs text-muted-foreground">Policy</p>
                  <p className="font-mono text-sm font-medium">{result?.policy_id}</p>
                </div>
              </div>

              <div className="rounded-md bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-800 dark:text-green-200 space-y-2">
                <p><strong>What was created:</strong></p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Zone <Badge variant="outline">LAN Server</Badge> with your network CIDR</li>
                  <li>Group <Badge variant="outline">All</Badge> for default full access</li>
                  <li>Policy: All → LAN Server = <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">allow</Badge></li>
                </ul>
              </div>

              <div className="rounded-md bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 px-4 py-3 text-sm text-blue-800 dark:text-blue-200">
                <Info className="h-4 w-4 inline mr-1" />
                <strong>Next steps:</strong> Add peers from the Peers page. They'll automatically get access to all networks. To restrict access, remove them from "All" and add to specific groups.
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={() => navigate("/")}>
                Go to Dashboard
              </Button>
            </CardFooter>
          </>
        )}
      </Card>
    </div>
  );
}
