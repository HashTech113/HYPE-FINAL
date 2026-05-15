import { createFileRoute } from "@tanstack/react-router";
import { RoleLoginPanel } from "@/components/auth/RoleLoginPanel";

type AdminLoginSearch = { redirect?: string };

export const Route = createFileRoute("/login/admin")({
  validateSearch: (search: Record<string, unknown>): AdminLoginSearch => ({
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
  component: AdminLoginPage,
});

function AdminLoginPage() {
  const { redirect } = Route.useSearch();
  return <RoleLoginPanel role="admin" redirect={redirect} />;
}
