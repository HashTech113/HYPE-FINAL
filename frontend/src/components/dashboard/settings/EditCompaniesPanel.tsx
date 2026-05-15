import { useCallback, useEffect, useRef, useState } from "react";
import {
  Building2,
  Eye,
  EyeOff,
  KeyRound,
  Pencil,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import {
  type Company,
  deleteCompany,
  getCompanies,
  renameCompany,
  resetAdminUserPassword,
  updateAdminUser,
} from "@/api/dashboardApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { useEmployees } from "@/contexts/EmployeesContext";

export function EditCompaniesPanel() {
  // Renames cascade backend-side into Employee.company / User.company,
  // but the global EmployeesContext is cached in memory + localStorage
  // — calling reload() after a successful rename refetches that cache so
  // Dashboard / Employees / Reports / Attendance immediately reflect the
  // new company name without a full page refresh.
  const { reload: reloadEmployees } = useEmployees();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [savingCompany, setSavingCompany] = useState(false);

  const [editingUsername, setEditingUsername] = useState<Company | null>(null);
  const [usernameDraft, setUsernameDraft] = useState("");
  const [savingUsername, setSavingUsername] = useState(false);

  const [resettingPassword, setResettingPassword] = useState<Company | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetEyeOn, setResetEyeOn] = useState(false);
  const [resettingBusy, setResettingBusy] = useState(false);
  const [resetConfirmation, setResetConfirmation] = useState<string | null>(null);

  const [deleting, setDeleting] = useState<Company | null>(null);
  const [deletingBusy, setDeletingBusy] = useState(false);

  // Toast suppression: the previous panel used a green strip; sonner is
  // already mounted at the app root so we switch to toasts here for
  // consistency with the cameras panel.
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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
      const list = await getCompanies();
      setCompanies(list);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load companies");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // --------------------------------------------------------------------
  // Company rename
  // --------------------------------------------------------------------

  const openCompanyEdit = (company: Company) => {
    setEditingCompany(company);
    setCompanyName(company.name);
  };

  const closeCompanyEdit = () => {
    if (savingCompany) return;
    setEditingCompany(null);
    setCompanyName("");
  };

  const handleSaveCompanyName = async () => {
    if (!editingCompany) return;
    const trimmed = companyName.trim();
    if (!trimmed) {
      toast.error("Company name cannot be empty");
      return;
    }
    if (trimmed === editingCompany.name) {
      closeCompanyEdit();
      return;
    }
    setSavingCompany(true);
    try {
      const updated = await renameCompany(editingCompany.id, trimmed);
      setCompanies((prev) =>
        prev
          .map((c) => (c.id === updated.id ? { ...c, ...updated } : c))
          .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" })),
      );
      // Cascade the rename into the app-wide employee cache so Dashboard,
      // Employees, Reports, and Attendance pick up the new company name
      // immediately. The backend has already updated employees.company /
      // users.company by string; this just makes the frontend re-fetch.
      reloadEmployees();
      toast.success(
        `Renamed to ${updated.name}. ${updated.employeeCount} employee${
          updated.employeeCount === 1 ? "" : "s"
        } updated.`,
      );
      setEditingCompany(null);
      setCompanyName("");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Rename failed");
    } finally {
      setSavingCompany(false);
    }
  };

  // --------------------------------------------------------------------
  // HR username rename
  // --------------------------------------------------------------------

  const openUsernameEdit = (company: Company) => {
    setEditingUsername(company);
    setUsernameDraft(company.hrUsername ?? "");
  };

  const closeUsernameEdit = () => {
    if (savingUsername) return;
    setEditingUsername(null);
    setUsernameDraft("");
  };

  const handleSaveUsername = async () => {
    if (!editingUsername || !editingUsername.hrUserId) {
      toast.error("No HR account linked to this company");
      return;
    }
    const trimmed = usernameDraft.trim();
    if (!trimmed) {
      toast.error("Username cannot be empty");
      return;
    }
    if (trimmed === editingUsername.hrUsername) {
      closeUsernameEdit();
      return;
    }
    setSavingUsername(true);
    try {
      const updated = await updateAdminUser(editingUsername.hrUserId, {
        username: trimmed,
      });
      setCompanies((prev) =>
        prev.map((c) =>
          c.hrUserId === updated.id
            ? { ...c, hrUsername: updated.username, hrUserActive: updated.isActive }
            : c,
        ),
      );
      toast.success(`Updated HR username to ${updated.username}`);
      setEditingUsername(null);
      setUsernameDraft("");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Username update failed");
    } finally {
      setSavingUsername(false);
    }
  };

  // --------------------------------------------------------------------
  // Password reset
  // --------------------------------------------------------------------

  const openPasswordReset = (company: Company) => {
    if (!company.hrUserId) {
      toast.error("No HR account linked — create one from User Accounts first");
      return;
    }
    setResettingPassword(company);
    setNewPassword("");
    setResetEyeOn(false);
    setResetConfirmation(null);
  };

  const closePasswordReset = () => {
    if (resettingBusy) return;
    setResettingPassword(null);
    setNewPassword("");
    setResetEyeOn(false);
    setResetConfirmation(null);
  };

  const handleResetPassword = async () => {
    if (!resettingPassword?.hrUserId) return;
    if (newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setResettingBusy(true);
    try {
      await resetAdminUserPassword(resettingPassword.hrUserId, newPassword);
      toast.success(`Password reset for ${resettingPassword.hrUsername}`);
      // Stay open in confirmation mode so the admin can copy the password
      // before it disappears. We surface the plaintext that was *just* sent
      // to the server one final time — it is never stored in cleartext on
      // either side, and this view is purely client-side memory.
      setResetConfirmation(newPassword);
      setResetEyeOn(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Password reset failed");
    } finally {
      setResettingBusy(false);
    }
  };

  const handleCopyPassword = async () => {
    if (!resetConfirmation) return;
    try {
      await navigator.clipboard.writeText(resetConfirmation);
      toast.success("Password copied to clipboard");
    } catch {
      toast.error("Copy failed — select the text and copy manually");
    }
  };

  // --------------------------------------------------------------------
  // Delete
  // --------------------------------------------------------------------

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setDeletingBusy(true);
    try {
      await deleteCompany(deleting.id);
      const removed = deleting;
      setCompanies((prev) => prev.filter((c) => c.id !== removed.id));
      toast.success(`Deleted ${removed.name}`);
      setDeleting(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Delete failed");
    } finally {
      setDeletingBusy(false);
    }
  };

  // --------------------------------------------------------------------
  // Render
  // --------------------------------------------------------------------

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <Building2 className="h-5 w-5 text-primary" />
          Edit Companies
        </h2>
        <div className="flex items-center gap-2 self-start rounded-lg border border-slate-200 bg-white px-3 py-1.5 sm:ml-auto sm:self-auto">
          <Building2 className="h-4 w-4 text-primary" />
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Total Companies:
          </span>
          <span className="text-sm font-bold text-slate-900">
            {loading ? "…" : companies.length}
          </span>
        </div>
      </div>

      {loadError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {loadError}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-auto rounded-xl border border-slate-200 bg-white">
        <Table className="min-w-[820px]">
          <TableHeader>
            <TableRow className="bg-slate-50/60">
              <TableHead className="w-14">S/N</TableHead>
              <TableHead className="text-indigo-700">Company</TableHead>
              <TableHead className="w-[110px] text-emerald-700">Employees</TableHead>
              <TableHead className="w-[120px] text-slate-700">HR Account</TableHead>
              <TableHead className="w-[180px] text-sky-700">User Name</TableHead>
              <TableHead className="w-[160px] text-amber-700">Password</TableHead>
              <TableHead className="w-[140px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {companies.map((company, index) => {
              const hasHr = !!company.hrUserId;
              return (
                <TableRow key={company.id} className="hover:bg-slate-50/60">
                  <TableCell className="text-slate-500">{index + 1}</TableCell>
                  <TableCell className="font-medium text-indigo-700">
                    {company.name}
                  </TableCell>
                  <TableCell className="font-medium text-emerald-700">
                    {company.employeeCount}
                  </TableCell>
                  <TableCell>
                    {hasHr ? (
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                          company.hrUserActive
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-slate-100 text-slate-500",
                        )}
                      >
                        <span
                          className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            company.hrUserActive ? "bg-emerald-500" : "bg-slate-400",
                          )}
                        />
                        {company.hrUserActive ? "Active" : "Disabled"}
                      </span>
                    ) : (
                      <span className="text-xs italic text-slate-400">None</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sky-700">
                    {hasHr ? (
                      <span className="font-mono text-xs">{company.hrUsername}</span>
                    ) : (
                      <span className="text-xs italic text-slate-400">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {hasHr ? (
                      <span
                        className="font-mono text-sm tracking-widest text-slate-700"
                        title="Stored as a one-way bcrypt hash — use the key icon to set a new password"
                      >
                        ••••••••
                      </span>
                    ) : (
                      <span className="text-xs italic text-slate-400">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-sky-700 hover:bg-sky-50 hover:text-sky-800"
                        onClick={() => openCompanyEdit(company)}
                        title="Rename company"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-indigo-700 hover:bg-indigo-50 hover:text-indigo-800 disabled:opacity-40"
                        onClick={() => openUsernameEdit(company)}
                        disabled={!hasHr}
                        title={
                          hasHr
                            ? "Edit HR username"
                            : "No HR account linked"
                        }
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-amber-700 hover:bg-amber-50 hover:text-amber-800 disabled:opacity-40"
                        onClick={() => openPasswordReset(company)}
                        disabled={!hasHr}
                        title={
                          hasHr
                            ? "Reset HR password"
                            : "No HR account linked"
                        }
                      >
                        <KeyRound className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:bg-rose-50 hover:text-destructive"
                        onClick={() => setDeleting(company)}
                        title="Delete company"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
            {!loading && companies.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="py-10 text-center text-muted-foreground"
                >
                  No companies yet.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>


      {/* --- Rename company dialog --- */}
      <Dialog
        open={editingCompany !== null}
        onOpenChange={(open) => !open && closeCompanyEdit()}
      >
        <DialogContent
          className="max-w-sm"
          onOpenAutoFocus={(event) => event.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>Rename Company</DialogTitle>
            <DialogDescription>
              Updates this company everywhere — employee records, HR account
              scope, and dropdown choices across the app.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="company-name">New name</Label>
            <Input
              id="company-name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  void handleSaveCompanyName();
                }
              }}
            />
            {editingCompany && editingCompany.employeeCount > 0 ? (
              <p className="text-xs text-muted-foreground">
                Will apply to {editingCompany.employeeCount} employee record
                {editingCompany.employeeCount === 1 ? "" : "s"}
                {editingCompany.hasUsers ? " and the linked HR account" : ""}.
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeCompanyEdit} disabled={savingCompany}>
              Cancel
            </Button>
            <Button onClick={handleSaveCompanyName} disabled={savingCompany}>
              {savingCompany ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* --- Rename HR username dialog --- */}
      <Dialog
        open={editingUsername !== null}
        onOpenChange={(open) => !open && closeUsernameEdit()}
      >
        <DialogContent
          className="max-w-sm"
          onOpenAutoFocus={(event) => event.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>Edit HR Username</DialogTitle>
            <DialogDescription>
              Renames the HR account linked to{" "}
              <span className="font-medium">{editingUsername?.name}</span>. The
              user must use the new username at next login.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="hr-username">New username</Label>
            <Input
              id="hr-username"
              value={usernameDraft}
              onChange={(e) => setUsernameDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  void handleSaveUsername();
                }
              }}
              autoComplete="off"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeUsernameEdit} disabled={savingUsername}>
              Cancel
            </Button>
            <Button onClick={handleSaveUsername} disabled={savingUsername}>
              {savingUsername ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* --- Reset password dialog (eye toggle lives here, on the actual input) --- */}
      <Dialog
        open={resettingPassword !== null}
        onOpenChange={(open) => !open && closePasswordReset()}
      >
        <DialogContent
          className="max-w-sm"
          onOpenAutoFocus={(event) => event.preventDefault()}
        >
          {resetConfirmation === null ? (
            <>
              <DialogHeader>
                <DialogTitle>Reset HR Password</DialogTitle>
                <DialogDescription>
                  Sets a new password for{" "}
                  <span className="font-mono">{resettingPassword?.hrUsername}</span> at{" "}
                  <span className="font-medium">{resettingPassword?.name}</span>. Tell the
                  user the new password out-of-band — we can't recover it later.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-2 py-2">
                <Label htmlFor="hr-password">New password</Label>
                <div className="relative">
                  <Input
                    id="hr-password"
                    type={resetEyeOn ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    autoComplete="new-password"
                    className="pr-9"
                    minLength={6}
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600"
                    onClick={() => setResetEyeOn((prev) => !prev)}
                    tabIndex={-1}
                    aria-label={resetEyeOn ? "Hide password" : "Show password"}
                  >
                    {resetEyeOn ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={closePasswordReset}
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
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>Password reset — copy it now</DialogTitle>
                <DialogDescription>
                  New password for{" "}
                  <span className="font-mono">{resettingPassword?.hrUsername}</span> at{" "}
                  <span className="font-medium">{resettingPassword?.name}</span>. This is the{" "}
                  <span className="font-semibold text-amber-700">only time</span> the
                  plaintext is shown — the server stores a one-way hash and cannot recover
                  it. Save it to a password manager before closing.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-2 py-2">
                <Label>Password</Label>
                <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <code className="flex-1 select-all break-all font-mono text-sm text-amber-900">
                    {resetConfirmation}
                  </code>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCopyPassword}
                    className="shrink-0"
                  >
                    Copy
                  </Button>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={closePasswordReset}>Done</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* --- Delete company alert --- */}
      <AlertDialog
        open={deleting !== null}
        onOpenChange={(open) => {
          if (!open && !deletingBusy) setDeleting(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete company?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleting
                ? deleting.employeeCount > 0
                  ? `${deleting.name} still has ${deleting.employeeCount} employee${
                      deleting.employeeCount === 1 ? "" : "s"
                    }. Reassign or delete them first — the server will block this.`
                  : `Permanently delete ${deleting.name}? ${
                      deleting.hasUsers
                        ? "The linked HR account will lose its company scope."
                        : ""
                    }`
                : "Delete this company?"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deletingBusy}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={deletingBusy}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deletingBusy ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
