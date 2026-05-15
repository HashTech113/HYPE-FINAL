import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, KeyRound, Pencil, Plus, ShieldOff, ShieldCheck, UserCog } from "lucide-react";

import {
  type AdminUser,
  type AdminUserCreate,
  createAdminUser,
  getAdminUsers,
  resetAdminUserPassword,
  updateAdminUser,
} from "@/api/dashboardApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type CreateState = AdminUserCreate;

const blankCreate = (): CreateState => ({
  username: "",
  role: "hr",
  company: "",
  displayName: "",
  password: "",
});

export function UsersPanel() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [addOpen, setAddOpen] = useState<boolean>(false);
  const [draft, setDraft] = useState<CreateState>(blankCreate());
  const [creating, setCreating] = useState<boolean>(false);
  const [generatedPassword, setGeneratedPassword] = useState<{
    username: string;
    password: string;
  } | null>(null);

  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [editDraft, setEditDraft] = useState<{
    role: "admin" | "hr";
    company: string;
    displayName: string;
    isActive: boolean;
  } | null>(null);
  const [savingEdit, setSavingEdit] = useState<boolean>(false);

  const [resetting, setResetting] = useState<AdminUser | null>(null);
  const [newPassword, setNewPassword] = useState<string>("");
  const [resettingBusy, setResettingBusy] = useState<boolean>(false);

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
    successTimerRef.current = setTimeout(() => setSuccessMessage(null), 4000);
  };
  useEffect(
    () => () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current);
    },
    [],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setUsers(await getAdminUsers());
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleCreate = async () => {
    const username = draft.username.trim();
    if (!username) {
      window.alert("Username is required.");
      return;
    }
    if (draft.role === "hr" && !draft.company.trim()) {
      window.alert("HR users must have a company.");
      return;
    }
    setCreating(true);
    try {
      const result = await createAdminUser({
        username,
        role: draft.role,
        company: draft.company.trim(),
        displayName: draft.displayName.trim() || username,
        password: draft.password?.trim() || undefined,
      });
      setUsers((prev) =>
        [...prev, result].sort((a, b) => a.username.localeCompare(b.username)),
      );
      if (result.generatedPassword) {
        setGeneratedPassword({
          username: result.username,
          password: result.generatedPassword,
        });
      } else {
        showSuccess(`Created user ${result.username}.`);
      }
      setAddOpen(false);
      setDraft(blankCreate());
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Create failed");
    } finally {
      setCreating(false);
    }
  };

  const openEdit = (u: AdminUser) => {
    setEditing(u);
    setEditDraft({
      role: u.role,
      company: u.company,
      displayName: u.displayName,
      isActive: u.isActive,
    });
  };

  const handleSaveEdit = async () => {
    if (!editing || !editDraft) return;
    setSavingEdit(true);
    try {
      const updated = await updateAdminUser(editing.id, {
        role: editDraft.role,
        company: editDraft.role === "hr" ? editDraft.company.trim() : "",
        displayName: editDraft.displayName.trim() || editing.username,
        isActive: editDraft.isActive,
      });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      showSuccess(`Updated ${updated.username}.`);
      setEditing(null);
      setEditDraft(null);
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleToggleActive = async (u: AdminUser) => {
    try {
      const updated = await updateAdminUser(u.id, { isActive: !u.isActive });
      setUsers((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
      showSuccess(`${updated.username} is now ${updated.isActive ? "active" : "disabled"}.`);
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Toggle failed");
    }
  };

  const handleResetPassword = async () => {
    if (!resetting) return;
    if (newPassword.length < 6) {
      window.alert("Password must be at least 6 characters.");
      return;
    }
    setResettingBusy(true);
    try {
      await resetAdminUserPassword(resetting.id, newPassword);
      showSuccess(`Password reset for ${resetting.username}.`);
      setResetting(null);
      setNewPassword("");
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Reset failed");
    } finally {
      setResettingBusy(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {successMessage ? (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-sm font-medium text-emerald-700"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <UserCog className="h-5 w-5 text-primary" />
          User Accounts
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {loading ? "Loading…" : `${users.length} user${users.length === 1 ? "" : "s"}`}
          </span>
          <Button size="sm" className="h-10 gap-1.5 px-4" onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4" />
            New User
          </Button>
        </div>
      </div>

      {loadError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {loadError}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-auto">
        <Table className="min-w-[720px]">
          <TableHeader>
            <TableRow className="bg-slate-50/60">
              <TableHead className="w-14">S/N</TableHead>
              <TableHead>Username</TableHead>
              <TableHead>Display Name</TableHead>
              <TableHead className="w-[100px]">Role</TableHead>
              <TableHead className="w-[160px]">Company</TableHead>
              <TableHead className="w-[100px]">Status</TableHead>
              <TableHead className="w-[160px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u, index) => (
              <TableRow key={u.id} className="hover:bg-slate-50/60">
                <TableCell className="text-slate-500">{index + 1}</TableCell>
                <TableCell className="font-medium text-slate-900">{u.username}</TableCell>
                <TableCell className="text-slate-700">{u.displayName}</TableCell>
                <TableCell>
                  <span
                    className={
                      u.role === "admin"
                        ? "inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-purple-700"
                        : "inline-flex rounded-full bg-sky-100 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-sky-700"
                    }
                  >
                    {u.role}
                  </span>
                </TableCell>
                <TableCell className="text-indigo-700">{u.company || "—"}</TableCell>
                <TableCell>
                  <span
                    className={
                      u.isActive
                        ? "inline-flex items-center gap-1 text-xs font-medium text-emerald-700"
                        : "inline-flex items-center gap-1 text-xs font-medium text-slate-400"
                    }
                  >
                    <span
                      className={`h-2 w-2 rounded-full ${
                        u.isActive ? "bg-emerald-500" : "bg-slate-300"
                      }`}
                    />
                    {u.isActive ? "Active" : "Disabled"}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-sky-700 hover:bg-sky-50 hover:text-sky-800"
                      onClick={() => openEdit(u)}
                      title="Edit user"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-amber-700 hover:bg-amber-50 hover:text-amber-800"
                      onClick={() => {
                        setResetting(u);
                        setNewPassword("");
                      }}
                      title="Reset password"
                    >
                      <KeyRound className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={
                        u.isActive
                          ? "h-8 w-8 text-rose-700 hover:bg-rose-50 hover:text-rose-800"
                          : "h-8 w-8 text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
                      }
                      onClick={() => handleToggleActive(u)}
                      title={u.isActive ? "Disable user" : "Enable user"}
                    >
                      {u.isActive ? (
                        <ShieldOff className="h-3.5 w-3.5" />
                      ) : (
                        <ShieldCheck className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {!loading && users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                  No users yet.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <Dialog
        open={addOpen}
        onOpenChange={(open) => {
          if (!open && !creating) {
            setAddOpen(false);
            setDraft(blankCreate());
          }
        }}
      >
        <DialogContent
          className="max-w-md"
          onOpenAutoFocus={(event) => event.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>New User Account</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-3 py-2">
            <div className="space-y-1.5">
              <Label>Username</Label>
              <Input
                value={draft.username}
                onChange={(e) => setDraft({ ...draft, username: e.target.value })}
                placeholder="e.g., wawu_hr_2"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Display name</Label>
              <Input
                value={draft.displayName}
                onChange={(e) => setDraft({ ...draft, displayName: e.target.value })}
                placeholder="Shown in the UI"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Role</Label>
                <Select
                  value={draft.role}
                  onValueChange={(value) =>
                    setDraft({ ...draft, role: value as "admin" | "hr" })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hr">HR</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Company {draft.role === "hr" ? "(required)" : "(ignored for admin)"}</Label>
                <Input
                  value={draft.company}
                  onChange={(e) => setDraft({ ...draft, company: e.target.value })}
                  placeholder="e.g., WAWU"
                  disabled={draft.role !== "hr"}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Password (optional)</Label>
              <Input
                type="text"
                value={draft.password ?? ""}
                onChange={(e) => setDraft({ ...draft, password: e.target.value })}
                placeholder="Leave blank to auto-generate a strong one"
              />
              <p className="text-xs text-muted-foreground">
                Auto-generated passwords are shown to you once after creation.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)} disabled={creating}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={creating}>
              {creating ? "Creating…" : "Create User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={generatedPassword !== null}
        onOpenChange={(open) => !open && setGeneratedPassword(null)}
      >
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Save this password</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2 text-sm">
            <p className="text-slate-700">
              Created <span className="font-semibold">{generatedPassword?.username}</span>. The
              auto-generated password is shown only once — copy it now.
            </p>
            <div className="select-all rounded-md border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-base text-slate-900">
              {generatedPassword?.password}
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setGeneratedPassword(null)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={editing !== null}
        onOpenChange={(open) => {
          if (!open && !savingEdit) {
            setEditing(null);
            setEditDraft(null);
          }
        }}
      >
        <DialogContent className="max-w-md" onOpenAutoFocus={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          {editing && editDraft ? (
            <div className="grid grid-cols-1 gap-3 py-2">
              <div className="text-sm text-muted-foreground">
                Username: <span className="font-mono">{editing.username}</span>
              </div>
              <div className="space-y-1.5">
                <Label>Display name</Label>
                <Input
                  value={editDraft.displayName}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, displayName: e.target.value })
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Role</Label>
                  <Select
                    value={editDraft.role}
                    onValueChange={(value) =>
                      setEditDraft({ ...editDraft, role: value as "admin" | "hr" })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hr">HR</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Company</Label>
                  <Input
                    value={editDraft.company}
                    onChange={(e) =>
                      setEditDraft({ ...editDraft, company: e.target.value })
                    }
                    disabled={editDraft.role !== "hr"}
                  />
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={editDraft.isActive}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, isActive: e.target.checked })
                  }
                />
                Account is active
              </label>
            </div>
          ) : null}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditing(null);
                setEditDraft(null);
              }}
              disabled={savingEdit}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={savingEdit}>
              {savingEdit ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={resetting !== null}
        onOpenChange={(open) => {
          if (!open && !resettingBusy) {
            setResetting(null);
            setNewPassword("");
          }
        }}
      >
        <DialogContent className="max-w-sm" onOpenAutoFocus={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Reset Password</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <p className="text-sm text-slate-600">
              Set a new password for{" "}
              <span className="font-semibold">{resetting?.username}</span>. The user must
              be told the new password out-of-band.
            </p>
            <Input
              type="text"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 6 characters"
              minLength={6}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setResetting(null);
                setNewPassword("");
              }}
              disabled={resettingBusy}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={resettingBusy || newPassword.length < 6}
            >
              {resettingBusy ? "Resetting…" : "Reset Password"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
