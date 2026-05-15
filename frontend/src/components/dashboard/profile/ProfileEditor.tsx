import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Camera, Eye, EyeOff, KeyRound, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import {
  changePassword,
  getAdminProfile,
  subscribeToAdminProfile,
  updateAdminProfile,
  type AdminProfile,
} from "@/lib/auth";

// Shared, role-agnostic profile editor. The PUT /api/auth/profile endpoint
// only ever updates the calling user's row, so admin and HR can use the same
// component without leaking access scope.
const MAX_AVATAR_BYTES = 2 * 1024 * 1024;

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "A";
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

export function useProfile(): AdminProfile {
  const [profile, setProfile] = useState<AdminProfile>(() => getAdminProfile());
  useEffect(() => subscribeToAdminProfile(() => setProfile(getAdminProfile())), []);
  return profile;
}

type ProfileAvatarProps = {
  name: string;
  avatarUrl: string;
  className?: string;
};

export function ProfileAvatar({ name, avatarUrl, className }: ProfileAvatarProps) {
  const initials = useMemo(() => getInitials(name), [name]);
  return (
    <div
      className={cn(
        "relative grid place-items-center overflow-hidden rounded-full bg-gradient-to-br from-[#69baa7] via-[#4aa590] to-[#2f8f7b] font-semibold text-white ring-4 ring-white",
        className,
      )}
    >
      {avatarUrl ? (
        <img src={avatarUrl} alt={name} className="h-full w-full object-cover" />
      ) : (
        <span className="tracking-wide">{initials}</span>
      )}
    </div>
  );
}

type ProfileCardProps = {
  profile: AdminProfile;
  onEdit: () => void;
  onChangePassword: () => void;
  subtitle?: string | null;
};

export function ProfileCard({ profile, onEdit, onChangePassword, subtitle }: ProfileCardProps) {
  return (
    <div className="w-full max-w-xl">
      <div className="neu-surface flex flex-col items-center gap-5 rounded-2xl border border-slate-200 px-8 py-10 sm:px-10">
        <ProfileAvatar
          name={profile.displayName}
          avatarUrl={profile.avatarUrl}
          className="h-32 w-32 text-3xl"
        />
        <div className="text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            {profile.displayName}
          </h2>
          <p className="mt-1 text-sm text-slate-500">@{profile.username}</p>
          {subtitle ? (
            <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">{subtitle}</p>
          ) : null}
        </div>
        <div className="mt-2 flex flex-wrap items-center justify-center gap-2.5">
          <Button
            type="button"
            onClick={onEdit}
            className="h-10 gap-2 rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-5 text-sm font-semibold text-white transition-all hover:from-[#3f9382] hover:to-[#256f60]"
          >
            <Pencil className="h-4 w-4" />
            Edit Profile
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onChangePassword}
            className="h-10 gap-2 rounded-xl border-slate-200 bg-white px-5 text-sm font-semibold text-[#3f9382] hover:bg-[#eef7f4] hover:text-[#2f8f7b]"
          >
            <KeyRound className="h-4 w-4" />
            Change Password
          </Button>
        </div>
      </div>
    </div>
  );
}

type EditProfileDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profile: AdminProfile;
};

export function EditProfileDialog({ open, onOpenChange, profile }: EditProfileDialogProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [displayName, setDisplayName] = useState(profile.displayName);
  const [username, setUsername] = useState(profile.username);
  const [avatarUrl, setAvatarUrl] = useState(profile.avatarUrl);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setDisplayName(profile.displayName);
      setUsername(profile.username);
      setAvatarUrl(profile.avatarUrl);
      setError(null);
    }
  }, [open, profile]);

  const handleAvatarSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Please choose an image file.");
      return;
    }
    if (file.size > MAX_AVATAR_BYTES) {
      setError("Image is too large. Choose a file under 2 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setAvatarUrl(reader.result);
        setError(null);
      }
    };
    reader.onerror = () => setError("Could not read the selected image.");
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    const trimmedName = displayName.trim();
    const trimmedUsername = username.trim();
    if (!trimmedName) {
      setError("Display name is required.");
      return;
    }
    if (!trimmedUsername) {
      setError("Username is required.");
      return;
    }
    setSubmitting(true);
    try {
      await updateAdminProfile({
        displayName: trimmedName,
        username: trimmedUsername,
        avatarUrl,
      });
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update profile.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              <ProfileAvatar
                name={displayName || profile.displayName}
                avatarUrl={avatarUrl}
                className="h-24 w-24 text-2xl"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 grid h-9 w-9 place-items-center rounded-full bg-white text-[#3f9382] ring-1 ring-slate-200 transition-colors hover:bg-[#eef7f4]"
                aria-label="Upload logo"
                title="Upload logo"
              >
                <Camera className="h-4 w-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleAvatarSelected}
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="h-8 gap-1.5 rounded-lg border-slate-200 px-3 text-xs"
              >
                <Camera className="h-3.5 w-3.5" />
                Upload logo
              </Button>
              {avatarUrl ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setAvatarUrl("")}
                  className="h-8 gap-1.5 rounded-lg px-3 text-xs text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Remove
                </Button>
              ) : null}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-display-name" className="text-slate-700">
              Display name
            </Label>
            <Input
              id="profile-display-name"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Display name"
              className="h-10 rounded-xl border-slate-200 bg-white focus-visible:ring-[#3f9382]"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-username" className="text-slate-700">
              Username
            </Label>
            <Input
              id="profile-username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="username"
              autoComplete="off"
              className="h-10 rounded-xl border-slate-200 bg-white focus-visible:ring-[#3f9382]"
            />
            <p className="text-xs text-slate-500">
              Used to sign in. Updating it will rename the active session.
            </p>
          </div>

          {error ? (
            <div
              role="alert"
              className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs font-medium text-rose-700"
            >
              {error}
            </div>
          ) : null}

          <DialogFooter className="gap-2 pt-2 sm:gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="h-10 rounded-xl">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="h-10 rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-5 font-semibold text-white hover:from-[#3f9382] hover:to-[#256f60]"
            >
              Save changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

type ChangePasswordDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function ChangePasswordDialog({ open, onOpenChange }: ChangePasswordDialogProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setShowCurrent(false);
      setShowNew(false);
      setError(null);
      setSuccess(false);
    }
  }, [open]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(false);
    setSubmitting(true);

    const result = await changePassword(currentPassword, newPassword, confirmPassword);
    setSubmitting(false);

    if (result.ok) {
      setSuccess(true);
      setTimeout(() => onOpenChange(false), 900);
      return;
    }
    if (result.reason === "incorrect-current") {
      setError("The current password is incorrect.");
    } else if (result.reason === "too-short") {
      setError("New password must be at least 6 characters.");
    } else if (result.reason === "network") {
      setError("Could not reach the server. Please try again.");
    } else {
      setError("New password and confirmation do not match.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl">
        <DialogHeader>
          <DialogTitle>Change Password</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <PasswordField
            id="current-password"
            label="Current password"
            value={currentPassword}
            onChange={setCurrentPassword}
            visible={showCurrent}
            onToggleVisible={() => setShowCurrent((prev) => !prev)}
            autoComplete="current-password"
          />
          <PasswordField
            id="new-password"
            label="New password"
            value={newPassword}
            onChange={setNewPassword}
            visible={showNew}
            onToggleVisible={() => setShowNew((prev) => !prev)}
            autoComplete="new-password"
            hint="At least 6 characters."
          />
          <PasswordField
            id="confirm-password"
            label="Confirm new password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            visible={showNew}
            onToggleVisible={() => setShowNew((prev) => !prev)}
            autoComplete="new-password"
          />

          {error ? (
            <div
              role="alert"
              className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs font-medium text-rose-700"
            >
              {error}
            </div>
          ) : null}
          {success ? (
            <div
              role="status"
              className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-xs font-medium text-emerald-700"
            >
              Password updated successfully.
            </div>
          ) : null}

          <DialogFooter className="gap-2 pt-2 sm:gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="h-10 rounded-xl">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting || success}
              className="h-10 rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-5 font-semibold text-white hover:from-[#3f9382] hover:to-[#256f60]"
            >
              Update password
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

type PasswordFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  visible: boolean;
  onToggleVisible: () => void;
  autoComplete?: string;
  hint?: string;
};

function PasswordField({
  id, label, value, onChange, visible, onToggleVisible, autoComplete, hint,
}: PasswordFieldProps) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-slate-700">
        {label}
      </Label>
      <div className="relative">
        <Input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete={autoComplete}
          className="h-10 rounded-xl border-slate-200 bg-white pr-10 focus-visible:ring-[#3f9382]"
        />
        <button
          type="button"
          onClick={onToggleVisible}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-slate-400 transition-colors hover:text-slate-600"
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}
