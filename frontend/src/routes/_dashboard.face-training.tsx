import { createFileRoute, redirect } from "@tanstack/react-router";
import { ScanFace } from "lucide-react";

import { SectionShell } from "@/components/dashboard/SectionShell";
import { FaceTrainingPanel } from "@/components/dashboard/FaceTrainingPanel";
import { getCurrentRole } from "@/lib/auth";

export const Route = createFileRoute("/_dashboard/face-training")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: FaceTrainingPage,
});

function FaceTrainingPage() {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Face Training"
        icon={<ScanFace className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        contentClassName="flex min-h-0 flex-1 flex-col gap-4 p-4"
      >
        <FaceTrainingPanel />
      </SectionShell>
    </div>
  );
}
