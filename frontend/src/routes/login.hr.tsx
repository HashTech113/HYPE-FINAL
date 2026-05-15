import { createFileRoute } from "@tanstack/react-router";
import { RoleLoginPanel } from "@/components/auth/RoleLoginPanel";

type HrLoginSearch = { redirect?: string };

export const Route = createFileRoute("/login/hr")({
  validateSearch: (search: Record<string, unknown>): HrLoginSearch => ({
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
  component: HrLoginPage,
});

function HrLoginPage() {
  const { redirect } = Route.useSearch();
  return <RoleLoginPanel role="hr" redirect={redirect} />;
}
