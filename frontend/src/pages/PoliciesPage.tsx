import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { policiesApi } from "@/api/networks";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X, Minus } from "lucide-react";

export function PoliciesPage() {
  const qc = useQueryClient();

  const { data: matrix, isLoading } = useQuery({
    queryKey: ["policy-matrix"],
    queryFn: () => policiesApi.matrix().then((r) => r.data),
  });

  const upsert = useMutation({
    mutationFn: ({ group_id, zone_id, action }: { group_id: number; zone_id: number; action: "allow" | "deny" }) =>
      policiesApi.upsert(group_id, zone_id, action),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policy-matrix"] }),
  });

  const remove = useMutation({
    mutationFn: (policy_id: number) => policiesApi.delete(policy_id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policy-matrix"] }),
  });

  const handleCellClick = (group_id: number, zone_id: number, current: "allow" | "deny" | null, policy_id: number | null) => {
    if (current === null) {
      upsert.mutate({ group_id, zone_id, action: "allow" });
    } else if (current === "allow") {
      upsert.mutate({ group_id, zone_id, action: "deny" });
    } else {
      // deny -> remove
      if (policy_id) remove.mutate(policy_id);
    }
  };

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading matrix...</p>;
  if (!matrix) return null;

  const { groups, zone_ids, zone_names } = matrix;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Access Policy Matrix</CardTitle>
          <CardDescription>
            Click a cell to cycle: <span className="text-green-600 font-medium">allow</span> → <span className="text-destructive font-medium">deny</span> → no rule.
            Precedence: deny_manual &gt; allow_manual &gt; deny_group &gt; allow_group &gt; no access.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {groups.length === 0 || zone_ids.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              Create groups and zones first to define policies.
            </p>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-muted/40">
                  <th className="text-left px-4 py-2 font-medium border-b border-r min-w-[160px]">Group</th>
                  {zone_ids.map((zid) => (
                    <th key={zid} className="px-4 py-2 font-medium border-b text-center whitespace-nowrap">
                      {zone_names[zid]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((row) => (
                  <tr key={row.group_id} className="border-b last:border-0 hover:bg-muted/10">
                    <td className="px-4 py-2 font-medium font-mono text-xs border-r">{row.group_name}</td>
                    {zone_ids.map((zid) => {
                      const cell = row.zones[zid];
                      const action = cell?.action ?? null;
                      const policy_id = cell?.policy_id ?? null;

                      return (
                        <td key={zid} className="px-4 py-2 text-center">
                          <button
                            onClick={() => handleCellClick(row.group_id, zid, action, policy_id)}
                            className={cn(
                              "inline-flex items-center justify-center w-8 h-8 rounded-md transition-colors border",
                              action === "allow" && "bg-green-100 border-green-300 text-green-700 hover:bg-green-200",
                              action === "deny" && "bg-red-100 border-red-300 text-red-700 hover:bg-red-200",
                              action === null && "bg-muted border-border text-muted-foreground hover:bg-accent"
                            )}
                            title={action === null ? "No rule (click to allow)" : action === "allow" ? "Allow (click to deny)" : "Deny (click to remove)"}
                          >
                            {action === "allow" && <Check className="h-4 w-4" />}
                            {action === "deny" && <X className="h-4 w-4" />}
                            {action === null && <Minus className="h-3 w-3" />}
                          </button>
                        </td>
                      );
                    })}
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
