import { useState } from "react";
import { UserCog } from "lucide-react";

import {
  ChangePasswordDialog,
  EditProfileDialog,
  ProfileCard,
  useProfile,
} from "@/components/dashboard/profile/ProfileEditor";

export function EditProfilePanel() {
  const profile = useProfile();
  const [editOpen, setEditOpen] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
        <UserCog className="h-5 w-5 text-primary" />
        Edit Profile
      </h2>
      <div className="flex flex-col items-center justify-center gap-6 py-2">
        <ProfileCard
          profile={profile}
          onEdit={() => setEditOpen(true)}
          onChangePassword={() => setPasswordOpen(true)}
        />
      </div>
      <EditProfileDialog open={editOpen} onOpenChange={setEditOpen} profile={profile} />
      <ChangePasswordDialog open={passwordOpen} onOpenChange={setPasswordOpen} />
    </div>
  );
}
