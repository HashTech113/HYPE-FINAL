import { Link, useNavigate, useRouter } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, Eye, EyeOff, Lock, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import {
  isAuthenticated,
  signIn,
  type AuthRole,
} from "@/lib/auth";
import hypeLogo from "@/images/HYPE_logo.png";

type RoleLoginPanelProps = {
  role: AuthRole;
  redirect?: string;
};

const ROLE_LABEL: Record<AuthRole, string> = {
  admin: "Admin",
  hr: "HR",
};

export function RoleLoginPanel({ role, redirect }: RoleLoginPanelProps) {
  const navigate = useNavigate();
  const router = useRouter();
  const roleLabel = ROLE_LABEL[role];

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Only auto-bounce when a `redirect` is present (i.e., user was sent here
  // by an auth-gated route). Direct visits to /login/admin or /login/hr keep
  // showing the form even with a cached token, so the app always starts at
  // the login page each session.
  useEffect(() => {
    if (redirect && isAuthenticated()) {
      void navigate({ to: redirect });
    }
  }, [navigate, redirect]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const result = await signIn(role, username, password);
      if (result) {
        router.invalidate();
        await navigate({ to: redirect ?? "/home" });
      } else {
        setError("Invalid username or password");
      }
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f3f4f6] px-4 py-10">
      <div
        key={role}
        className="animate-auth-from-right relative z-10 grid w-full max-w-5xl overflow-hidden rounded-[28px] bg-white/70 shadow-[0_30px_60px_rgba(12,70,56,0.18)] backdrop-blur-xl md:grid-cols-2"
      >
        {/* Brand panel — matches the sidebar gradient + tagline used across the app. */}
        <aside className="relative hidden flex-col justify-between bg-gradient-to-b from-[#69baa7] via-[#4aa590] to-[#2f8f7b] p-10 text-white md:flex">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-30"
            style={{
              backgroundImage:
                "radial-gradient(circle at 20% 20%, rgba(255,255,255,0.35), transparent 45%), radial-gradient(circle at 80% 70%, rgba(255,255,255,0.18), transparent 50%)",
            }}
          />
          <div className="relative">
            <img
              src={hypeLogo}
              alt="HYPE logo"
              className="h-24 w-24 object-contain drop-shadow-[0_6px_18px_rgba(0,0,0,0.18)]"
            />
            <h1 className="mt-8 text-3xl font-semibold leading-tight tracking-wide">
              Welcome, {roleLabel}
            </h1>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-white/85">
              Log in to continue to the Movement Intelligence Platform — your
              real-time view of attendance, presence, and team activity.
            </p>
          </div>

          <div className="relative mt-10">
            <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-white/70">
              Movement Intelligence Platform
            </p>
            <p className="mt-2 text-xs text-white/65">
              Secure {role === "admin" ? "admin" : "HR"} access · Internal tooling
            </p>
          </div>
        </aside>

        {/* Form panel */}
        <section className="flex flex-col justify-center p-8 sm:p-10 md:p-12">
          {/* Compact brand header — only shows when the brand panel is hidden. */}
          <div className="mb-6 flex items-center gap-3 md:hidden">
            <img src={hypeLogo} alt="HYPE logo" className="h-12 w-12 object-contain" />
            <div>
              <p className="text-sm font-semibold tracking-wide text-[#3f9382]">
                Movement Intelligence Platform
              </p>
              <p className="text-xs text-slate-500">{roleLabel} sign-in</p>
            </div>
          </div>

          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
                {roleLabel} Login
              </h2>
              <p className="mt-1.5 text-sm text-slate-500">
                Enter your credentials to access the dashboard.
              </p>
            </div>
            <Link
              to="/login"
              search={redirect ? { redirect } : undefined}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
              title="Choose a different role"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back
            </Link>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="username" className="text-slate-700">
                Username
              </Label>
              <div className="relative">
                <UserIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  id="username"
                  type="text"
                  autoComplete="username"
                  autoFocus
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder={role === "admin" ? "admin" : "your company username"}
                  className="h-11 rounded-xl border-slate-200 bg-white pl-10 text-sm shadow-sm focus-visible:ring-[#3f9382]"
                  disabled={submitting}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-slate-700">
                Password
              </Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  className="h-11 rounded-xl border-slate-200 bg-white pl-10 pr-10 text-sm shadow-sm focus-visible:ring-[#3f9382]"
                  disabled={submitting}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-slate-400 transition-colors hover:text-slate-600"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div
              role="alert"
              aria-live="polite"
              className={cn(
                "rounded-xl border px-3 py-2.5 text-xs font-medium transition-all duration-200",
                error
                  ? "border-rose-200 bg-rose-50 text-rose-700 opacity-100"
                  : "pointer-events-none -mt-1 border-transparent opacity-0",
              )}
            >
              {error ?? " "}
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="h-11 w-full rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] text-sm font-semibold tracking-wide text-white shadow-[0_10px_24px_rgba(47,143,123,0.32)] transition-all hover:from-[#3f9382] hover:to-[#256f60] hover:shadow-[0_14px_30px_rgba(47,143,123,0.42)] disabled:opacity-70"
            >
              {submitting ? "Signing in…" : "Login"}
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">
            {role === "admin"
              ? "Restricted access. For authorized administrators only."
              : "Restricted access. For authorized HR personnel only."}
          </p>
        </section>
      </div>
    </div>
  );
}
