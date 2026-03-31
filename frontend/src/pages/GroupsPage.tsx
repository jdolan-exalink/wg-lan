import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { groupsApi } from "@/api/networks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export function GroupsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const create = useMutation({
    mutationFn: (data: FormData) => groupsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["groups"] }); setShowForm(false); },
  });

  const del = useMutation({
    mutationFn: (id: number) => groupsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["groups"] }),
  });

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Access profiles — assign peers to groups to inherit policies</p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Group
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">New Group</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit((d) => create.mutateAsync(d).then(() => reset()))} className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Name</Label>
                <Input placeholder="rw_planta_ventas" {...register("name")} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1">
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
                <th className="text-left px-4 py-2 font-medium">Description</th>
                <th className="text-left px-4 py-2 font-medium">Members</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {groups.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No groups yet</td></tr>
              ) : groups.map((g) => (
                <tr key={g.id} className="border-b last:border-0 hover:bg-muted/20">
                  <td className="px-4 py-2 font-medium font-mono text-xs">{g.name}</td>
                  <td className="px-4 py-2 text-muted-foreground">{g.description ?? "—"}</td>
                  <td className="px-4 py-2">
                    <Badge variant="secondary">{g.member_count} peer{g.member_count !== 1 ? "s" : ""}</Badge>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Button variant="ghost" size="icon" onClick={() => del.mutate(g.id)}>
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
