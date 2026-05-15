import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  Settings as SettingsIcon,
  Users,
  CalendarCheck,
  UserCog,
  Building2,
} from "lucide-react";

import { SectionShell } from "@/components/dashboard/SectionShell";
import { cn } from "@/lib/utils";
import { getCurrentRole } from "@/lib/auth";

import { EditEmployeesPanel } from "@/components/dashboard/settings/EditEmployeesPanel";
import { EditAttendancePanel } from "@/components/dashboard/settings/EditAttendancePanel";
import { EditProfilePanel } from "@/components/dashboard/settings/EditProfilePanel";
import { EditCompaniesPanel } from "@/components/dashboard/settings/EditCompaniesPanel";

export const Route = createFileRoute("/_dashboard/settings")({
  component: SettingsPage,
});

type TabId = "employees" | "companies" | "attendance" | "profile";

type TabDef = { id: TabId; label: string; icon: typeof Users; adminOnly?: boolean };

const TABS: TabDef[] = [
  { id: "employees", label: "Edit Employee Management", icon: Users },
  { id: "companies", label: "Edit Companies", icon: Building2, adminOnly: true },
  { id: "attendance", label: "Edit Attendance Report", icon: CalendarCheck },
  { id: "profile", label: "Edit Profile", icon: UserCog },
];

function SettingsPage() {
  const role = getCurrentRole();
  const visibleTabs = TABS.filter((t) => !t.adminOnly || role === "admin");
  const [active, setActive] = useState<TabId>("employees");

  const tabBar = (
    <div
      role="tablist"
      aria-label="Settings sections"
      // Mobile: full-width column of stacked tabs so the long labels never
      // collide with the page title. From sm+ they line up horizontally and
      // optically center under the header, with the desktop-only nudge that
      // keeps them visually balanced against the section icon + title.
      className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center sm:justify-center md:mx-auto md:-translate-x-16"
    >
      {visibleTabs.map((tab) => {
        const Icon = tab.icon;
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => setActive(tab.id)}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-colors sm:w-auto sm:justify-start",
              selected
                ? "border-[#3f9382] bg-[#eef7f4] text-[#2f8f7b]"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-800",
            )}
          >
            <Icon className="h-4 w-4" />
            {tab.label}
          </button>
        );
      })}
    </div>
  );

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Settings"
        icon={<SettingsIcon className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        contentClassName="flex min-h-0 flex-1 flex-col gap-4 p-4"
        inlineActions
        actions={tabBar}
      >
        <div className="scrollbar-hidden flex min-h-0 flex-1 flex-col overflow-y-auto pr-1">
          {active === "employees" ? <EditEmployeesPanel /> : null}
          {active === "companies" && role === "admin" ? <EditCompaniesPanel /> : null}
          {active === "attendance" ? <EditAttendancePanel /> : null}
          {active === "profile" ? <EditProfilePanel /> : null}
        </div>
      </SectionShell>
    </div>
  );
}
