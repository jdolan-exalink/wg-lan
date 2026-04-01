import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { policiesApi, groupsApi } from "@/api/networks";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, ArrowRight, ArrowLeft, ArrowLeftRight, Check, X, Minus, Trash2 } from "lucide-react";
import type { Policy, PeerGroup } from "@/types/network";

const directionIcons: Record<string, React.ReactNode> = {
  outbound: <ArrowRight className="h-3 w-3" />,
  inbound: <ArrowLeft className="h-3 w-3" />,
  both: <ArrowLeftRight className="h-3 w-3" />,
};

const directionLabels: Record<string, string> = {
  outbound: "Outbound (source → dest)",
  inbound: "Inbound (dest → source)",
  both: "Both directions",
};

export function PoliciesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [sourceGroupId, setSourceGroupId] = useState<string>("");
  const [destGroupId, setDestGroupId] = useState<string>("");
  const [direction, setDirection] = useState<"outbound" | "inbound" | "both">("both");
  const [action, setAction] = useState<"allow" | "deny">("allow");

  const { data: policies = [], isLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: () => policiesApi.list().then((r) => r.data),
  });

  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const createPolicy = useMutation({
    mutationFn: (data: { source_group_id: number; dest_group_id: number; direction: string; action: string }) =>
      policiesApi.create(data as any),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["policies"] });
      setShowForm(false);
      setSourceGroupId("");
      setDestGroupId("");
    },
  });

  const deletePolicy = useMutation({
    mutationFn: (id: number) => policiesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  const toggleAction = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "allow" | "deny" }) =>
      policiesApi.update(id, { action }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  const handleSubmit = () => {
    if (!sourceGroupId || !destGroupId) return;
    createPolicy.mutate({
      source_group_id: parseInt(sourceGroupId),
      dest_group_id: parseInt(destGroupId),
      direction,
      action,
    });
  };

  const getGroupName = (id: number) => groups.find((g: PeerGroup) => g.id === id)?.name || `Group ${id}`;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {policies.length} policies configured — group-to-group access control
        </p>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add Policy
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">New Policy</CardTitle>
            <CardDescription>
              Define access between groups. Source group members can reach dest group's networks based on direction.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Source Group</label>
                <Select value={sourceGroupId} onValueChange={setSourceGroupId}>
                  <SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger>
                  <SelectContent>
                    {groups.map((g: PeerGroup) => (
                      <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Dest Group</label>
                <Select value={destGroupId} onValueChange={setDestGroupId}>
                  <SelectTrigger><SelectValue placeholder="Select dest" /></SelectTrigger>
                  <SelectContent>
                    {groups.map((g: PeerGroup) => (
                      <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Direction</label>
                <Select value={direction} onValueChange={(v) => setDirection(v as any)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="outbound">Outbound →</SelectItem>
                    <SelectItem value="inbound">Inbound ←</SelectItem>
                    <SelectItem value="both">Both ↔</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Action</label>
                <Select value={action} onValueChange={(v) => setAction(v as any)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="allow">Allow</SelectItem>
                    <SelectItem value="deny">Deny</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end gap-2">
                <Button size="sm" onClick={handleSubmit} disabled={!sourceGroupId || !destGroupId || createPolicy.isPending}>
                  {createPolicy.isPending ? "Saving..." : "Save"}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Policy List</CardTitle>
          <CardDescription>
            Click action to toggle allow ↔ deny. Direction controls which group can reach which networks.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {policies.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              No policies yet. Create groups first, then define policies between them.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium">Source Group</th>
                  <th className="text-left px-4 py-2 font-medium">Direction</th>
                  <th className="text-left px-4 py-2 font-medium">Dest Group</th>
                  <th className="text-left px-4 py-2 font-medium">Action</th>
                  <th className="text-right px-4 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {policies.map((p: Policy) => (
                  <tr key={p.id} className="border-b last:border-0 hover:bg-muted/10">
                    <td className="px-4 py-2 font-mono text-xs">{p.source_group_name || getGroupName(p.source_group_id)}</td>
                    <td className="px-4 py-2">
                      <Badge variant="outline" className="text-xs flex items-center gap-1 w-fit">
                        {directionIcons[p.direction]}
                        {directionLabels[p.direction]}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">{p.dest_group_name || getGroupName(p.dest_group_id)}</td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => toggleAction.mutate({ id: p.id, action: p.action === "allow" ? "deny" : "allow" })}
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                          p.action === "allow"
                            ? "bg-green-100 text-green-700 hover:bg-green-200"
                            : "bg-red-100 text-red-700 hover:bg-red-200"
                        }`}
                      >
                        {p.action === "allow" ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        {p.action.toUpperCase()}
                      </button>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deletePolicy.mutate(p.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
