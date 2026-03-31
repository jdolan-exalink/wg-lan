import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { networksApi } from "@/api/networks";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2 } from "lucide-react";
import type { Network } from "@/types/network";

const schema = z.object({
  name: z.string().min(1, "Required"),
  subnet: z.string().regex(/^\d+\.\d+\.\d+\.\d+\/\d+$/, "Invalid CIDR"),
  description: z.string().optional(),
  is_default: z.boolean().default(false),
});
type FormData = z.infer<typeof schema>;

export function NetworksPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: networks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  const create = useMutation({
    mutationFn: (data: FormData) => networksApi.create(data as Omit<Network, "id">),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["networks"] }); setShowForm(false); },
  });

  const del = useMutation({
    mutationFn: (id: number) => networksApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    await create.mutateAsync(data);
    reset();
  };

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">VPN tunnel subnets used for peer IP assignment</p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Network
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">New Network</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Name</Label>
                <Input placeholder="VPN Principal" {...register("name")} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1">
                <Label>Subnet (CIDR)</Label>
                <Input placeholder="10.50.0.0/24" {...register("subnet")} />
                {errors.subnet && <p className="text-xs text-destructive">{errors.subnet.message}</p>}
              </div>
              <div className="space-y-1 col-span-2">
                <Label>Description</Label>
                <Input placeholder="Optional" {...register("description")} />
              </div>
              <div className="col-span-2 flex gap-2">
                <Button type="submit" size="sm" disabled={isSubmitting}>Save</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2 font-medium">Name</th>
                <th className="text-left px-4 py-2 font-medium">Subnet</th>
                <th className="text-left px-4 py-2 font-medium">Description</th>
                <th className="text-left px-4 py-2 font-medium">Default</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {networks.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No networks yet</td></tr>
              ) : networks.map((n) => (
                <tr key={n.id} className="border-b last:border-0 hover:bg-muted/20">
                  <td className="px-4 py-2 font-medium">{n.name}</td>
                  <td className="px-4 py-2 font-mono text-xs">{n.subnet}</td>
                  <td className="px-4 py-2 text-muted-foreground">{n.description ?? "—"}</td>
                  <td className="px-4 py-2">{n.is_default && <Badge variant="success">Default</Badge>}</td>
                  <td className="px-4 py-2 text-right">
                    <Button variant="ghost" size="icon" onClick={() => del.mutate(n.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
