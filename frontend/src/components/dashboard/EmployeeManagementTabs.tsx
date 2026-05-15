import { Link, useLocation } from "@tanstack/react-router";
import { Clock, FileText, Users } from "lucide-react";
import type { ComponentType } from "react";

import { getCurrentRole } from "@/lib/auth";
import { cn } from "@/lib/utils";

type Tab = {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

const TABS: Tab[] = [
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/employees", label: "Employees", icon: Users },
  { to: "/presence", label: "Attendance History", icon: Clock },
];

/** Admin-only horizontal tab strip shown above the Employee Management
 * sub-pages (Employees / Attendance History / Reports / Face Training).
 * Renders nothing for non-admin users so HR's existing layout is
 * unchanged. */
export function EmployeeManagementTabs() {
  const role = getCurrentRole();
  const location = useLocation();

  if (role !== "admin") return null;

  const path = location.pathname;

  return (
    <div
      role="tablist"
      aria-label="Employee management sections"
      className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center sm:justify-center sm:mx-auto"
    >
      {TABS.map((tab) => {
        const Icon = tab.icon;
        const active = path === tab.to;
        return (
          <Link
            key={tab.to}
            to={tab.to}
            role="tab"
            aria-selected={active}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-colors sm:w-auto sm:justify-start",
              active
                ? "border-[#3f9382] bg-[#eef7f4] text-[#2f8f7b]"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-800",
            )}
          >
            <Icon className="h-4 w-4" />
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
