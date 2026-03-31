import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { zonesApi } from "@/api/networks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  networks: z.array(z.object({ cidr: z.string().regex(/^\d+\.\d+\.\d+\.\d+\/\d+$/, "Invalid CIDR") })),
});
type FormData = z.infer<typeof schema>;

export function ZonesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const { data: zones = [] } = useQuery({
    queryKey: ["zones"],
    queryFn: () => zonesApi.list().then((r) => r.data),
  });

  const create = useMutation({
    mutationFn: (data: FormData) => zonesApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["zones"] }); setShowForm(false); },
  });

  const del = useMutation({
    mutationFn: (id: number) => zonesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["zones"] }),
  });

  const { register, handleSubmit, control, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { networks: [{ cidr: "" }] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "networks" });

  const toggle = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Logical access destinations (e.g., Planta, Ventas)</p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Zone
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle className="text-sm">New Zone</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit((d) => create.mutateAsync(d).then(() => reset()))} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label>Name</Label>
                  <Input placeholder="Planta" {...register("name")} />
                  {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                </div>
                <div className="space-y-1">
                  <Label>Description</Label>
                  <Input placeholder="Optional" {...register("description")} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Subnets</Label>
                {fields.map((f, i) => (
                  <div key={f.id} className="flex gap-2">
                    <Input placeholder="10.10.10.0/24" {...register(`networks.${i}.cidr`)} />
                    {fields.length > 1 && (
                      <Button type="button" variant="ghost" size="icon" onClick={() => remove(i)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button type="button" variant="outline" size="sm" onClick={() => append({ cidr: "" })}>
                  <Plus className="h-4 w-4" /> Add Subnet
                </Button>
              </div>
              <div className="flex gap-2">
                <Button type="submit" size="sm" disabled={isSubmitting}>Save</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {zones.length === 0 ? (
          <Card><CardContent className="py-8 text-center text-muted-foreground text-sm">No zones yet</CardContent></Card>
        ) : zones.map((z) => (
          <Card key={z.id}>
            <div
              className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-muted/20"
              onClick={() => toggle(z.id)}
            >
              <div className="flex items-center gap-2">
                {expanded.has(z.id) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                <span className="font-medium">{z.name}</span>
                <Badge variant="secondary">{z.networks.length} subnet{z.networks.length !== 1 ? "s" : ""}</Badge>
              </div>
              <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); del.mutate(z.id); }}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
            {expanded.has(z.id) && z.networks.length > 0 && (
              <CardContent className="pt-0 pb-3">
                <div className="flex flex-wrap gap-2 pl-6">
                  {z.networks.map((n) => (
                    <code key={n.id} className="text-xs bg-muted px-2 py-0.5 rounded">{n.cidr}</code>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
