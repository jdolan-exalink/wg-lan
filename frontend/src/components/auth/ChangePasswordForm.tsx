import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { authApi } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { KeyRound } from "lucide-react";

const schema = z.object({
  current_password: z.string().min(1, "Required"),
  new_password: z.string().min(8, "At least 8 characters"),
  confirm_password: z.string().min(1, "Required"),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type FormData = z.infer<typeof schema>;

export function ChangePasswordForm() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await authApi.changePassword(data.current_password, data.new_password);
      await refresh();
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to change password");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2">
            <KeyRound className="h-8 w-8 text-primary" />
          </div>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>You must set a new password before continuing</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1">
              <Label>Current Password</Label>
              <Input type="password" {...register("current_password")} />
              {errors.current_password && <p className="text-xs text-destructive">{errors.current_password.message}</p>}
            </div>
            <div className="space-y-1">
              <Label>New Password</Label>
              <Input type="password" {...register("new_password")} />
              {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
            </div>
            <div className="space-y-1">
              <Label>Confirm New Password</Label>
              <Input type="password" {...register("confirm_password")} />
              {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
            </div>
            {error && (
              <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
            )}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Set New Password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
