import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { DashboardLayout } from "@/components/DashboardLayout";
import { EmployeesProvider } from "@/contexts/EmployeesContext";
import { DashboardDataProvider } from "@/contexts/DashboardDataContext";
import { AttendanceSummariesProvider } from "@/contexts/AttendanceSummariesContext";
import { isAuthenticated } from "@/lib/auth";

export const Route = createFileRoute("/_dashboard")({
  beforeLoad: ({ location }) => {
    if (!isAuthenticated()) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: DashboardLayoutRoute,
});

function DashboardLayoutRoute() {
  return (
    <EmployeesProvider>
      <DashboardDataProvider>
        <AttendanceSummariesProvider>
          <DashboardLayout>
            <Outlet />
          </DashboardLayout>
        </AttendanceSummariesProvider>
      </DashboardDataProvider>
    </EmployeesProvider>
  );
}
