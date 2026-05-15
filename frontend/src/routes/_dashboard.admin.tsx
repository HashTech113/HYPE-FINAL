import { createFileRoute, redirect } from "@tanstack/react-router";
import { useState } from "react";
import { UserCog } from "lucide-react";

import { SectionShell } from "@/components/dashboard/SectionShell";
import {
  ChangePasswordDialog,
  EditProfileDialog,
  ProfileCard,
  useProfile,
} from "@/components/dashboard/profile/ProfileEditor";
import { getCurrentRole } from "@/lib/auth";

export const Route = createFileRoute("/_dashboard/admin")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: AdminManagementPage,
});

function AdminManagementPage() {
  const profile = useProfile();
  const [editOpen, setEditOpen] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Admin Management"
        icon={<UserCog className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
      >
        <div className="flex min-h-0 flex-1 items-start justify-center overflow-y-auto py-6">
          <ProfileCard
            profile={profile}
            subtitle="Administrator"
            onEdit={() => setEditOpen(true)}
            onChangePassword={() => setPasswordOpen(true)}
          />
        </div>
      </SectionShell>

      <EditProfileDialog open={editOpen} onOpenChange={setEditOpen} profile={profile} />
      <ChangePasswordDialog open={passwordOpen} onOpenChange={setPasswordOpen} />
    </div>
  );
}
