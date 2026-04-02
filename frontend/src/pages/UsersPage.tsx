import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi, groupsApi } from "@/api/users";
import { networksApi } from "@/api/networks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Search, UserX, UserCheck, KeyRound, Eye, Pencil, Loader2, Shield, ShieldAlert, Globe } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { User, GroupSummary, UserNetworkAssignment } from "@/api/users";

const userSchema = z.object({
  username: z.string().min(3, "Min 3 characters").max(50),
  email: z.string().email("Invalid email").or(z.literal("")).optional(),
  password: z.string().min(8, "Min 8 characters").max(128),
  password_confirm: z.string().min(8, "Min 8 characters").max(128),
  is_active: z.boolean().default(true),
  is_admin: z.boolean().default(false),
}).refine((data) => data.password === data.password_confirm, {
  message: "Passwords do not match",
  path: ["password_confirm"],
});
type UserFormData = z.infer<typeof userSchema>;

const resetPasswordSchema = z.object({
  new_password: z.string().min(8, "Min 8 characters").max(128),
  new_password_confirm: z.string().min(8, "Min 8 characters").max(128),
}).refine((data) => data.new_password === data.new_password_confirm, {
  message: "Passwords do not match",
  path: ["new_password_confirm"],
});
type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Never";
  return new Date(dateStr).toLocaleString();
}

export function UsersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [resettingUser, setResettingUser] = useState<User | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);
  const [managingGroupsUser, setManagingGroupsUser] = useState<User | null>(null);
  const [managingNetworksUser, setManagingNetworksUser] = useState<User | null>(null);
  const [assignNetworkUserId, setAssignNetworkUserId] = useState<number | null>(null);
  const [assignNetworkId, setAssignNetworkId] = useState<string>("");
  const [assignNetworkAction, setAssignNetworkAction] = useState<"allow" | "deny">("allow");
  const [assignNetworkError, setAssignNetworkError] = useState("");

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ["users", search],
    queryFn: () => usersApi.list({ search: search || undefined }).then((r) => r.data),
  });

  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupsApi.list().then((r) => r.data),
  });

  const { data: userGroups = [] } = useQuery({
    queryKey: ["user-groups", managingGroupsUser?.id],
    queryFn: () => managingGroupsUser ? usersApi.getGroups(managingGroupsUser.id).then((r) => r.data) : Promise.resolve([]),
    enabled: !!managingGroupsUser,
  });

  const { data: userNetworks = [] } = useQuery({
    queryKey: ["user-networks", managingNetworksUser?.id],
    queryFn: () => managingNetworksUser ? usersApi.getNetworks(managingNetworksUser.id).then((r) => r.data) : Promise.resolve([]),
    enabled: !!managingNetworksUser,
  });

  const { data: allNetworks = [] } = useQuery({
    queryKey: ["networks"],
    queryFn: () => networksApi.list().then((r) => r.data),
  });

  // ── Mutations ────────────────────────────────────────────────────────────
  const createUserMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setShowCreateDialog(false);
      createForm.reset();
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { email?: string; is_active?: boolean; is_admin?: boolean } }) =>
      usersApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setEditingUser(null);
    },
  });

  const disableUserMutation = useMutation({
    mutationFn: usersApi.disable,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const enableUserMutation = useMutation({
    mutationFn: usersApi.enable,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      usersApi.resetPassword(id, password),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setResettingUser(null);
      resetForm.reset();
    },
  });

  const assignGroupsMutation = useMutation({
    mutationFn: ({ userId, groupIds }: { userId: number; groupIds: number[] }) =>
      usersApi.assignGroups(userId, groupIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-groups"] });
      qc.invalidateQueries({ queryKey: ["users"] });
      setManagingGroupsUser(null);
    },
  });

  const assignNetworkMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: { network_id: number; action: string } }) =>
      usersApi.assignNetwork(userId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-networks"] });
      qc.invalidateQueries({ queryKey: ["users"] });
      setAssignNetworkUserId(null);
      setAssignNetworkId("");
      setAssignNetworkAction("allow");
      setAssignNetworkError("");
    },
    onError: (err: any) => {
      setAssignNetworkError(err?.response?.data?.detail ?? "Error al asignar red");
    },
  });

  const removeNetworkMutation = useMutation({
    mutationFn: ({ userId, networkId }: { userId: number; networkId: number }) =>
      usersApi.removeNetwork(userId, networkId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-networks"] });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });

  // ── Forms ────────────────────────────────────────────────────────────────
  const createForm = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      username: "",
      email: "",
      password: "",
      password_confirm: "",
      is_active: true,
      is_admin: false,
    },
  });

  const resetForm = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      new_password: "",
      new_password_confirm: "",
    },
  });

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleCreateUser = (data: UserFormData) => {
    createUserMutation.mutate({
      username: data.username,
      email: data.email || undefined,
      password: data.password,
      password_confirm: data.password_confirm,
      is_active: data.is_active,
      is_admin: data.is_admin,
    });
  };

  const handleToggleActive = (user: User) => {
    if (user.is_active) {
      disableUserMutation.mutate(user.id);
    } else {
      enableUserMutation.mutate(user.id);
    }
  };

  const handleResetPassword = (data: ResetPasswordFormData) => {
    if (resettingUser) {
      resetPasswordMutation.mutate({
        id: resettingUser.id,
        password: data.new_password,
      });
    }
  };

  const handleAssignGroups = (selectedGroupIds: number[]) => {
    if (managingGroupsUser) {
      assignGroupsMutation.mutate({
        userId: managingGroupsUser.id,
        groupIds: selectedGroupIds,
      });
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">Usuarios</h1>
          <p className="text-sm text-outline">Manage system users and their access</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create User
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-outline" />
            <Input
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          {usersLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-outline-variant/20">
                    <th className="text-left py-3 px-4 font-medium text-outline">Usuario</th>
                    <th className="text-left py-3 px-4 font-medium text-outline">Estado</th>
                    <th className="text-left py-3 px-4 font-medium text-outline">Rol</th>
                    <th className="text-left py-3 px-4 font-medium text-outline">Última conexión</th>
                    <th className="text-left py-3 px-4 font-medium text-outline">Creado</th>
                    <th className="text-right py-3 px-4 font-medium text-outline">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-outline-variant/10 hover:bg-surface-container-hover/50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-on-surface">{user.username}</div>
                          {user.email && (
                            <div className="text-xs text-outline">{user.email}</div>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={user.is_active ? "default" : "secondary"}>
                          {user.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {user.is_admin ? (
                          <Badge variant="outline">Admin</Badge>
                        ) : (
                          <span className="text-outline">User</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-outline">
                        {formatDate(user.last_login_at)}
                      </td>
                      <td className="py-3 px-4 text-outline">
                        {formatDate(user.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setViewingUser(user)}
                            title="View details"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingUser(user)}
                            title="Edit user"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setResettingUser(user)}
                            title="Reset password"
                          >
                            <KeyRound className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setManagingGroupsUser(user)}
                            title="Manage groups"
                          >
                            <UserCheck className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setManagingNetworksUser(user)}
                            title="Manage networks"
                          >
                            <Globe className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleActive(user)}
                            title={user.is_active ? "Deactivate" : "Activate"}
                          >
                            {user.is_active ? (
                              <UserX className="h-4 w-4 text-error" />
                            ) : (
                              <UserCheck className="h-4 w-4 text-tertiary" />
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Create User Dialog ──────────────────────────────────────────── */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create User</DialogTitle>
            <DialogDescription>Add a new user to the system</DialogDescription>
          </DialogHeader>
          <form onSubmit={createForm.handleSubmit(handleCreateUser)} className="space-y-4">
            <div>
              <Label>Username</Label>
              <Input {...createForm.register("username")} />
              {createForm.formState.errors.username && (
                <p className="text-xs text-error mt-1">{createForm.formState.errors.username.message}</p>
              )}
            </div>
            <div>
              <Label>Email (optional)</Label>
              <Input {...createForm.register("email")} type="email" />
              {createForm.formState.errors.email && (
                <p className="text-xs text-error mt-1">{createForm.formState.errors.email.message}</p>
              )}
            </div>
            <div>
              <Label>Password</Label>
              <Input {...createForm.register("password")} type="password" />
              {createForm.formState.errors.password && (
                <p className="text-xs text-error mt-1">{createForm.formState.errors.password.message}</p>
              )}
            </div>
            <div>
              <Label>Confirm Password</Label>
              <Input {...createForm.register("password_confirm")} type="password" />
              {createForm.formState.errors.password_confirm && (
                <p className="text-xs text-error mt-1">{createForm.formState.errors.password_confirm.message}</p>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="is_active"
                  checked={createForm.watch("is_active")}
                  onCheckedChange={(checked: boolean) => createForm.setValue("is_active", checked)}
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="is_admin"
                  checked={createForm.watch("is_admin")}
                  onCheckedChange={(checked: boolean) => createForm.setValue("is_admin", checked)}
                />
                <Label htmlFor="is_admin">Admin</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createUserMutation.isPending}>
                {createUserMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Create
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── Edit User Dialog ────────────────────────────────────────────── */}
      <Dialog open={!!editingUser} onOpenChange={(open) => !open && setEditingUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User: {editingUser?.username}</DialogTitle>
            <DialogDescription>Modify user settings and permissions</DialogDescription>
          </DialogHeader>
          {editingUser && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                updateUserMutation.mutate({
                  id: editingUser.id,
                  data: {
                    email: formData.get("email") as string || undefined,
                    is_active: formData.get("is_active") === "on",
                    is_admin: formData.get("is_admin") === "on",
                  },
                });
              }}
              className="space-y-4"
            >
              <div>
                <Label>Email</Label>
                <Input name="email" defaultValue={editingUser.email || ""} type="email" />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="edit_is_active"
                    name="is_active"
                    defaultChecked={editingUser.is_active}
                  />
                  <Label htmlFor="edit_is_active">Active</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="edit_is_admin"
                    name="is_admin"
                    defaultChecked={editingUser.is_admin}
                  />
                  <Label htmlFor="edit_is_admin">Admin</Label>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditingUser(null)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updateUserMutation.isPending}>
                  {updateUserMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Save
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Reset Password Dialog ───────────────────────────────────────── */}
      <Dialog open={!!resettingUser} onOpenChange={(open) => !open && setResettingUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password: {resettingUser?.username}</DialogTitle>
            <DialogDescription>The user will be required to change their password on next login</DialogDescription>
          </DialogHeader>
          <form onSubmit={resetForm.handleSubmit(handleResetPassword)} className="space-y-4">
            <div>
              <Label>New Password</Label>
              <Input {...resetForm.register("new_password")} type="password" />
              {resetForm.formState.errors.new_password && (
                <p className="text-xs text-error mt-1">{resetForm.formState.errors.new_password.message}</p>
              )}
            </div>
            <div>
              <Label>Confirm New Password</Label>
              <Input {...resetForm.register("new_password_confirm")} type="password" />
              {resetForm.formState.errors.new_password_confirm && (
                <p className="text-xs text-error mt-1">{resetForm.formState.errors.new_password_confirm.message}</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setResettingUser(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={resetPasswordMutation.isPending}>
                {resetPasswordMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Reset Password
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── Manage Groups Dialog ────────────────────────────────────────── */}
      <Dialog open={!!managingGroupsUser} onOpenChange={(open) => !open && setManagingGroupsUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Manage Groups: {managingGroupsUser?.username}</DialogTitle>
            <DialogDescription>Select groups to assign to this user</DialogDescription>
          </DialogHeader>
          {managingGroupsUser && (
            <div className="space-y-4">
              <div className="space-y-2">
                {groups.map((group) => {
                  const isSelected = userGroups.some((ug) => ug.id === group.id);
                  return (
                    <div key={group.id} className="flex items-center gap-2">
                      <Checkbox
                        id={`group-${group.id}`}
                        checked={isSelected}
                        onCheckedChange={(checked: boolean) => {
                          const currentIds = userGroups.map((ug) => ug.id);
                          if (checked) {
                            handleAssignGroups([...currentIds, group.id]);
                          } else {
                            handleAssignGroups(currentIds.filter((id) => id !== group.id));
                          }
                        }}
                      />
                      <Label htmlFor={`group-${group.id}`}>{group.name}</Label>
                    </div>
                  );
                })}
              </div>
              <DialogFooter>
                <Button onClick={() => setManagingGroupsUser(null)}>
                  Done
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Manage Networks Dialog ──────────────────────────────────────── */}
      <Dialog open={!!managingNetworksUser} onOpenChange={(open) => !open && setManagingNetworksUser(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Redes de Acceso: {managingNetworksUser?.username}</DialogTitle>
            <DialogDescription>
              Redes específicas asignadas a este usuario. Los peers del usuario heredarán este acceso.
            </DialogDescription>
          </DialogHeader>
          {managingNetworksUser && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <Button size="sm" onClick={() => { setAssignNetworkUserId(managingNetworksUser.id); setAssignNetworkId(""); setAssignNetworkAction("allow"); setAssignNetworkError(""); }}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Asignar red
                </Button>
              </div>
              {userNetworks.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  No hay redes asignadas directamente — el acceso se controla mediante grupos y políticas.
                </p>
              ) : (
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {userNetworks.map((a) => (
                    <div key={a.id} className="flex items-center gap-3 text-sm py-2 px-3 rounded bg-muted/20">
                      {a.action === "allow" ? (
                        <Shield className="h-4 w-4 text-green-500 shrink-0" />
                      ) : (
                        <ShieldAlert className="h-4 w-4 text-red-500 shrink-0" />
                      )}
                      <span className="font-medium">{a.network_name}</span>
                      <code className="font-mono text-muted-foreground bg-muted/40 px-1 rounded text-xs">{a.subnet}</code>
                      <Badge variant={a.action === "allow" ? "default" : "destructive"} className="text-[10px]">
                        {a.action === "allow" ? "Permitir" : "Denegar"}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">{a.network_type}</Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 ml-auto"
                        onClick={() => removeNetworkMutation.mutate({ userId: managingNetworksUser.id, networkId: a.network_id })}
                      >
                        <UserX className="h-3 w-3 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <DialogFooter>
                <Button onClick={() => setManagingNetworksUser(null)}>
                  Done
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Assign Network to User Dialog ───────────────────────────────── */}
      <Dialog open={assignNetworkUserId !== null} onOpenChange={(open) => {
        if (!open) { setAssignNetworkUserId(null); setAssignNetworkId(""); setAssignNetworkAction("allow"); setAssignNetworkError(""); }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Asignar red al usuario</DialogTitle>
            <DialogDescription>
              Seleccioná una red existente para asignar a este usuario. Los peers del usuario podrán acceder (o se les negará) a esta red.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <Label>Red de destino</Label>
              <Select value={assignNetworkId} onValueChange={setAssignNetworkId}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccioná una red..." />
                </SelectTrigger>
                <SelectContent>
                  {allNetworks.map((n: any) => (
                    <SelectItem key={n.id} value={String(n.id)}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{n.name}</span>
                        <code className="text-xs font-mono text-muted-foreground">{n.subnet}</code>
                        <Badge variant="outline" className="text-[10px]">{n.network_type}</Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Acción</Label>
              <Select value={assignNetworkAction} onValueChange={(v) => setAssignNetworkAction(v as "allow" | "deny")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="allow">
                    <div className="flex items-center gap-2">
                      <Shield className="h-3.5 w-3.5 text-green-500" />
                      <span>Permitir acceso</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="deny">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="h-3.5 w-3.5 text-red-500" />
                      <span>Denegar acceso</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            {assignNetworkError && (
              <p className="text-xs text-destructive">{assignNetworkError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignNetworkUserId(null)}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (assignNetworkUserId && assignNetworkId) {
                  assignNetworkMutation.mutate({
                    userId: assignNetworkUserId,
                    data: { network_id: parseInt(assignNetworkId), action: assignNetworkAction },
                  });
                }
              }}
              disabled={!assignNetworkId || assignNetworkMutation.isPending}
            >
              {assignNetworkMutation.isPending ? "Asignando..." : "Asignar red"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── View User Dialog ────────────────────────────────────────────── */}
      <Dialog open={!!viewingUser} onOpenChange={(open) => !open && setViewingUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>User Details: {viewingUser?.username}</DialogTitle>
            <DialogDescription>View user account information</DialogDescription>
          </DialogHeader>
          {viewingUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-outline">Username:</span>
                  <p className="font-medium">{viewingUser.username}</p>
                </div>
                <div>
                  <span className="text-outline">Email:</span>
                  <p className="font-medium">{viewingUser.email || "—"}</p>
                </div>
                <div>
                  <span className="text-outline">Status:</span>
                  <p>
                    <Badge variant={viewingUser.is_active ? "default" : "secondary"}>
                      {viewingUser.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </p>
                </div>
                <div>
                  <span className="text-outline">Role:</span>
                  <p>{viewingUser.is_admin ? "Admin" : "User"}</p>
                </div>
                <div>
                  <span className="text-outline">Last Login:</span>
                  <p>{formatDate(viewingUser.last_login_at)}</p>
                </div>
                <div>
                  <span className="text-outline">Failed Attempts:</span>
                  <p>{viewingUser.failed_login_count}</p>
                </div>
                <div>
                  <span className="text-outline">Created:</span>
                  <p>{formatDate(viewingUser.created_at)}</p>
                </div>
                <div>
                  <span className="text-outline">Updated:</span>
                  <p>{formatDate(viewingUser.updated_at)}</p>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setViewingUser(null)}>Close</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
