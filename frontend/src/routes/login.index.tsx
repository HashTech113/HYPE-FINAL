import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { ChevronRight, ShieldCheck, UserCog, Users } from "lucide-react";
import { isAuthenticated, type AuthRole } from "@/lib/auth";
import { cn } from "@/lib/utils";
import hypeLogo from "@/images/HYPE_logo.png";

type LoginIndexSearch = { redirect?: string };

export const Route = createFileRoute("/login/")({
  validateSearch: (search: Record<string, unknown>): LoginIndexSearch => ({
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
  component: RoleSelectionPage,
});

type RoleOption = {
  role: AuthRole;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
};

const ROLE_OPTIONS: RoleOption[] = [
  {
    role: "admin",
    title: "Admin",
    description: "Full access to settings and management",
    icon: UserCog,
  },
  {
    role: "hr",
    title: "HR",
    description: "Attendance, presence, and team activity",
    icon: Users,
  },
];

function RoleSelectionPage() {
  const navigate = useNavigate();
  const { redirect } = Route.useSearch();

  // Only auto-bounce when a `redirect` is present — that signals the user was
  // sent here by an auth-gated route and should land back there post-login.
  // Direct visits to /login always show the role chooser, even with a cached
  // token, so the app reliably starts on the login page each session.
  useEffect(() => {
    if (redirect && isAuthenticated()) {
      void navigate({ to: redirect });
    }
  }, [navigate, redirect]);

  const goToRole = (role: AuthRole) => {
    void navigate({
      to: role === "admin" ? "/login/admin" : "/login/hr",
      search: redirect ? { redirect } : undefined,
    });
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f3f4f6] px-4 py-10">
      <div className="animate-auth-from-left relative z-10 w-full max-w-md overflow-hidden rounded-[28px] bg-white/85 shadow-[0_30px_60px_rgba(12,70,56,0.18)] backdrop-blur-xl">
        {/* Header band — gradient accent matching the sidebar. */}
        <div className="relative bg-gradient-to-b from-[#69baa7] via-[#4aa590] to-[#2f8f7b] px-8 pb-8 pt-10 text-center text-white">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-30"
            style={{
              backgroundImage:
                "radial-gradient(circle at 30% 20%, rgba(255,255,255,0.4), transparent 50%), radial-gradient(circle at 80% 80%, rgba(255,255,255,0.18), transparent 55%)",
            }}
          />
          <div className="relative">
            <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-white/95 shadow-[0_12px_28px_rgba(12,70,56,0.28)] ring-4 ring-white/40">
              <img src={hypeLogo} alt="HYPE logo" className="h-14 w-14 object-contain" />
            </div>
            <h1 className="mt-5 text-2xl font-semibold tracking-tight">
              Welcome Back
            </h1>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-white/85">
              Log in to continue to the Movement Intelligence Platform — your
              real-time view of attendance, presence, and team activity.
            </p>
          </div>
        </div>

        <div className="px-7 py-7 sm:px-9">
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[#3f9382]" />
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
              Select Your Login
            </p>
          </div>

          <div className="space-y-3">
            {ROLE_OPTIONS.map((option) => (
              <button
                key={option.role}
                type="button"
                onClick={() => goToRole(option.role)}
                className={cn(
                  "group flex w-full items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-left transition-all duration-200",
                  "hover:-translate-y-0.5 hover:border-[#4aa590]/40 hover:shadow-[0_12px_28px_rgba(47,143,123,0.18)]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3f9382] focus-visible:ring-offset-2",
                )}
              >
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-[#69baa7] via-[#4aa590] to-[#2f8f7b] text-white shadow-[0_8px_18px_rgba(47,143,123,0.32)]">
                  <option.icon className="h-5 w-5" />
                </span>
                <span className="flex flex-1 flex-col">
                  <span className="text-sm font-semibold text-slate-900">
                    {option.title}
                  </span>
                  <span className="text-xs text-slate-500">{option.description}</span>
                </span>
                <ChevronRight className="h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-[#3f9382]" />
              </button>
            ))}
          </div>

          <div className="mt-7 border-t border-slate-100 pt-5 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
              Movement Intelligence Platform
            </p>
            <p className="mt-1.5 text-xs text-slate-400">
              Secure admin &amp; employee access · Internal tooling
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
