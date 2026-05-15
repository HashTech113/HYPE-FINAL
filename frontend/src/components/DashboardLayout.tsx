import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState, type ComponentType } from "react";
import {
  LayoutDashboard,
  Clock,
  MessageSquare,
  Settings,
  Users,
  UserX,
  FileText,
  Menu,
  LogOut,
  Camera as CameraIcon,
  Video,
  ScanFace,
} from "lucide-react";
import hypeLogo from "@/images/HYPE_logo.png";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getIngestLastSeen } from "@/api/dashboardApi";
import {
  getAdminProfile,
  getCurrentRole,
  signOut,
  subscribeToAdminProfile,
  type AdminProfile,
  type AuthRole,
} from "@/lib/auth";
import { cn } from "@/lib/utils";

// Notification-dot poll cadence. 10 s is responsive enough for a sidebar
// badge (a new capture being noticed within ten seconds is fine) while
// avoiding the per-route refetch storm a tighter interval caused — the
// poll fires on every mounted DashboardLayout, so navigating quickly
// between sections used to fire three or four 3 s polls back-to-back.
const INGEST_POLL_MS = 10_000;
const INGEST_DOT_VISIBLE_MS = 2_000;

type NavChild = {
  label: string;
  to: string;
  icon: ComponentType<{ className?: string }>;
  search?: Record<string, string>;
  /** Roles allowed to see this child. Undefined = all authenticated users. */
  roles?: AuthRole[];
};

type NavItem = {
  label: string;
  to: string;
  icon: ComponentType<{ className?: string }>;
  children?: NavChild[];
  /** Roles allowed to see this item. Undefined = all authenticated users. */
  roles?: AuthRole[];
};

const navItems: NavItem[] = [
  { label: "Dashboard", to: "/home", icon: LayoutDashboard },
  // HR-only items keep their pre-existing slot near the top of the HR view.
  { label: "Attendance History", to: "/presence", icon: Clock, roles: ["hr"] },
  { label: "Reports", to: "/reports", icon: FileText, roles: ["hr"] },
  { label: "Add Camera", to: "/cameras", icon: CameraIcon, roles: ["admin"] },
  { label: "Live Cameras", to: "/cameras/live", icon: Video, roles: ["admin"] },
  { label: "Face Training", to: "/face-training", icon: ScanFace, roles: ["admin"] },
  { label: "Live Captures", to: "/requests", icon: MessageSquare, roles: ["admin"] },
  { label: "Unknown Faces", to: "/unknown-faces", icon: UserX, roles: ["admin"] },
  { label: "Employee Management", to: "/employees", icon: Users },
  { label: "Settings", to: "/settings", icon: Settings },
];

function visibleForRole<T extends { roles?: AuthRole[] }>(item: T, role: AuthRole | null): boolean {
  if (!item.roles) return true;
  return role !== null && item.roles.includes(role);
}

function filterNavForRole(items: NavItem[], role: AuthRole | null): NavItem[] {
  return items
    .filter((item) => visibleForRole(item, role))
    .map((item) => ({
      ...item,
      children: item.children?.filter((child) => visibleForRole(child, role)),
    }));
}

function isParentActive(item: NavItem, pathname: string): boolean {
  if (pathname === item.to) return true;
  if (!item.children) return false;
  return item.children.some((child) => pathname === child.to);
}

function isChildActive(
  child: NavChild,
  pathname: string,
  searchRole: string | undefined,
): boolean {
  if (pathname !== child.to) return false;
  const expectedRole = child.search?.role;
  if (expectedRole === undefined) {
    return searchRole === undefined || searchRole === "all";
  }
  return searchRole === expectedRole;
}

function initialSidebarState(): boolean {
  if (typeof window === "undefined") return true;
  return window.innerWidth >= 1024;
}

function isMobileViewport(): boolean {
  if (typeof window === "undefined") return false;
  return window.innerWidth < 768;
}

type SidebarBodyProps = {
  expanded: boolean;
  pathname: string;
  searchRole: string | undefined;
  ingestFresh: boolean;
  navItems: NavItem[];
  displayName: string;
  subtitle: string | null;
  avatarUrl: string;
  onNavigate?: () => void;
  onLogout: () => void;
};

function getProfileInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "A";
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

function SidebarBody({
  expanded,
  pathname,
  searchRole,
  ingestFresh,
  navItems,
  displayName,
  subtitle,
  avatarUrl,
  onNavigate,
  onLogout,
}: SidebarBodyProps) {
  return (
    <>
      <nav
        className={cn(
          "relative z-10 mt-2 flex flex-1 flex-col gap-3",
          expanded ? "w-full items-stretch" : "w-full items-center",
        )}
      >
        {navItems.map((item) => {
          const parentActive = isParentActive(item, pathname);
          const selfActive = pathname === item.to;
          // Only flag Live Captures when the backend has seen a recent
          // capture (driven by /api/ingest/last-seen → !stale).
          const showNotificationDot = item.to === "/requests" && ingestFresh;
          const showChildren = expanded && item.children && item.children.length > 0;

          return (
            <div
              key={item.to}
              className={cn(expanded ? "w-full" : "flex w-full justify-center")}
            >
              <Link
                to={item.to}
                onClick={onNavigate}
                className={cn(
                  "relative transition-all duration-200",
                  expanded
                    ? "flex h-10 w-full items-center gap-3 rounded-xl px-3"
                    : "flex h-10 w-10 items-center justify-center rounded-xl",
                  selfActive || (!expanded && parentActive)
                    ? "bg-white text-[#3f9382] shadow-[0_10px_20px_rgba(12,70,56,0.22)]"
                    : "text-white/90 hover:bg-white/18 hover:text-white",
                )}
                title={item.label}
              >
                <item.icon className="h-4 w-4" />
                <span
                  className={cn(
                    "truncate text-sm font-medium transition-all duration-200",
                    expanded
                      ? "max-w-[160px] opacity-100"
                      : "pointer-events-none max-w-0 opacity-0",
                  )}
                >
                  {item.label}
                </span>
                {showNotificationDot ? (
                  // Flash even when the operator is already on this route — the
                  // dot confirms a fresh capture just landed, which is exactly
                  // the feedback they want while they're looking at the list.
                  <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-[#ffe37d]" />
                ) : null}
              </Link>

              {showChildren ? (
                <div className="mt-1 flex flex-col gap-1 pl-5">
                  {item.children!.map((child) => {
                    const childActive = isChildActive(child, pathname, searchRole);
                    return (
                      <Link
                        key={`${child.to}-${child.search?.role ?? "default"}`}
                        to={child.to}
                        search={child.search}
                        onClick={onNavigate}
                        className={cn(
                          "flex h-9 w-full items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors",
                          childActive
                            ? "bg-white/90 text-[#3f9382] shadow-sm"
                            : "text-white/85 hover:bg-white/15 hover:text-white",
                        )}
                        title={child.label}
                      >
                        <child.icon className="h-3.5 w-3.5" />
                        <span className="truncate">{child.label}</span>
                      </Link>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
      </nav>

      <div className={cn("relative z-10 mt-4 w-full pb-1", expanded ? "px-1" : "px-2")}>
        <div
          className={cn(
            "flex w-full items-center px-2 py-1.5 text-white/95",
            expanded ? "justify-between gap-2" : "flex-col gap-2",
          )}
        >
          <div className={cn("flex items-center", expanded ? "gap-3" : "flex-col")}>
            <Avatar className="h-8 w-8 bg-slate-50 ring-2 ring-white/40">
              {avatarUrl ? <AvatarImage src={avatarUrl} alt={displayName} /> : null}
              <AvatarFallback className="bg-slate-50 text-xs font-semibold text-[#3f9382]">
                {getProfileInitials(displayName)}
              </AvatarFallback>
            </Avatar>
            <div
              className={cn(
                "flex min-w-0 flex-col leading-tight transition-all duration-200",
                expanded
                  ? "max-w-[140px] opacity-100"
                  : "pointer-events-none max-w-0 opacity-0",
              )}
            >
              <span className="truncate text-sm font-medium text-white">{displayName}</span>
              {subtitle ? (
                <span className="truncate text-[10px] uppercase tracking-wider text-white/70">
                  {subtitle}
                </span>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout}
            title="Sign out"
            aria-label="Sign out"
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-white/85 transition-colors hover:bg-white/18 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );
}

const SIDEBAR_ASIDE_CLASSES =
  "relative flex min-h-0 w-full flex-1 flex-col rounded-r-[28px] bg-gradient-to-b from-[#69baa7] via-[#4aa590] to-[#2f8f7b] py-5 transition-[padding] duration-300 ease-out";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarExpanded, setSidebarExpanded] = useState(initialSidebarState);
  const [ingestFresh, setIngestFresh] = useState(false);
  const [profile, setProfile] = useState<AdminProfile>(() => getAdminProfile());

  // Read role once at mount — the layout only renders post-auth and unmounts
  // on sign-out, so a fresh read on the next sign-in is guaranteed.
  const role = getCurrentRole();

  // Keep the sidebar / header avatar synced with profile edits — HR can
  // now edit their profile too via Settings → Edit Profile, so the
  // subscription must run for both roles.
  useEffect(() => {
    return subscribeToAdminProfile(() => setProfile(getAdminProfile()));
  }, []);

  const handleLogout = () => {
    signOut();
    void navigate({ to: "/login" });
  };

  // Resolve the display name + subtitle shown next to the sidebar avatar.
  // The cached AuthUser already carries displayName + company, so HR rows
  // don't need a separate credential lookup.
  const sidebarDisplay = (() => {
    if (role === "admin") {
      return { name: profile.displayName, subtitle: null as string | null, avatarUrl: profile.avatarUrl };
    }
    if (role === "hr") {
      return {
        name: profile.displayName || "HR",
        subtitle: null as string | null,
        avatarUrl: profile.avatarUrl,
      };
    }
    return { name: "User", subtitle: null as string | null, avatarUrl: "" };
  })();

  const visibleNavItems = filterNavForRole(navItems, role);

  const searchRole =
    typeof (location.search as { role?: string }).role === "string"
      ? ((location.search as { role?: string }).role as string)
      : undefined;

  // Close the mobile overlay whenever the route changes.
  useEffect(() => {
    if (isMobileViewport()) {
      setSidebarExpanded(false);
    }
  }, [location.pathname, location.search]);

  // Drive the Live Captures notification dot as a transient "new capture"
  // indicator. The dot lights up only when ``last_seen`` advances between
  // polls (i.e. a fresh capture has arrived since the last check) and
  // self-clears after INGEST_DOT_VISIBLE_MS. The backend's stale window
  // is intentionally ignored here — a stale heartbeat shouldn't show the
  // dot, only a brand-new capture should.
  const lastSeenRef = useRef<string | null>(null);
  const dotTimerRef = useRef<number | null>(null);
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      // Skip while tab is hidden so background tabs don't keep
      // hammering the API while the user is in another app.
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const status = await getIngestLastSeen();
        if (cancelled) return;
        const advanced =
          !!status.last_seen &&
          !status.stale &&
          status.last_seen !== lastSeenRef.current;
        // On the very first poll we initialise the ref but don't flash —
        // otherwise every page reload would show the dot regardless of
        // whether a capture had actually arrived since last visit.
        if (lastSeenRef.current === null) {
          lastSeenRef.current = status.last_seen;
          return;
        }
        if (advanced) {
          lastSeenRef.current = status.last_seen;
          setIngestFresh(true);
          if (dotTimerRef.current !== null) {
            window.clearTimeout(dotTimerRef.current);
          }
          dotTimerRef.current = window.setTimeout(() => {
            setIngestFresh(false);
            dotTimerRef.current = null;
          }, INGEST_DOT_VISIBLE_MS);
        }
      } catch {
        if (!cancelled) setIngestFresh(false);
      }
    };
    void tick();
    const id = setInterval(tick, INGEST_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
      if (dotTimerRef.current !== null) {
        window.clearTimeout(dotTimerRef.current);
        dotTimerRef.current = null;
      }
    };
  }, []);

  const closeMobileSidebar = () => {
    if (isMobileViewport()) {
      setSidebarExpanded(false);
    }
  };

  return (
    <div className="relative h-screen overflow-hidden bg-[#f3f4f6]">
      <div className="mx-auto flex h-full max-w-[1680px] flex-col px-2 py-2 sm:px-3 sm:py-3 md:px-4 md:py-4">
        <header className="relative flex h-[62px] shrink-0 items-center border-b border-slate-200/60 bg-[#f3f4f6] px-2 sm:px-3 md:px-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarExpanded((prev) => !prev)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-700 transition-colors hover:bg-slate-200/60 hover:text-slate-900"
              aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
              title={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
            >
              <Menu className="h-5 w-5" />
            </button>
            {sidebarExpanded ? (
              <img
                src={hypeLogo}
                alt="HYPE logo"
                className="h-20 w-20 shrink-0 object-contain sm:h-24 sm:w-24"
              />
            ) : null}
          </div>

          <p className="pointer-events-none absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-base font-semibold tracking-wide text-[#3f9382] sm:text-lg md:text-2xl lg:text-3xl xl:text-4xl">
            ᴍᴏᴠᴇᴍᴇɴᴛ ɪɴᴛᴇʟʟɪɢᴇɴᴄᴇ ᴘʟᴀᴛꜰᴏʀᴍ
          </p>

          <div className="ml-auto flex items-center gap-1.5 text-slate-700">
            {role === "admin" ? (
              <Link
                to="/admin"
                className="flex flex-col items-center px-1 py-1 text-slate-700 transition-colors hover:text-slate-900 sm:px-2 sm:py-1.5"
                aria-label="Admin profile"
                title={sidebarDisplay.name}
              >
                <div className="grid h-9 w-9 place-items-center overflow-hidden rounded-full bg-[#4aa590] text-xs font-semibold text-white shadow-sm sm:h-10 sm:w-10">
                  {sidebarDisplay.avatarUrl ? (
                    <img
                      src={sidebarDisplay.avatarUrl}
                      alt={sidebarDisplay.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="sm:text-sm">{getProfileInitials(sidebarDisplay.name)}</span>
                  )}
                </div>
              </Link>
            ) : (
              <div
                className="flex items-center gap-2 px-1 py-1 text-slate-700 sm:px-2 sm:py-1.5"
                title={sidebarDisplay.name}
              >
                <div className="grid h-9 w-9 place-items-center overflow-hidden rounded-full bg-[#4aa590] text-xs font-semibold text-white shadow-sm sm:h-10 sm:w-10">
                  <span className="sm:text-sm">{getProfileInitials(sidebarDisplay.name)}</span>
                </div>
                {sidebarDisplay.subtitle ? (
                  <span className="hidden text-xs font-semibold uppercase tracking-wider text-slate-500 sm:inline">
                    {sidebarDisplay.subtitle}
                  </span>
                ) : null}
              </div>
            )}
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1 overflow-hidden rounded-2xl bg-white">
          {/* Desktop / tablet sidebar — in flow, push layout */}
          <div
            className={cn(
              "relative z-10 hidden h-full shrink-0 flex-col transition-[width] duration-300 ease-out md:flex",
              sidebarExpanded ? "md:w-[248px]" : "md:w-[92px]",
            )}
          >
            <aside
              className={cn(
                SIDEBAR_ASIDE_CLASSES,
                sidebarExpanded ? "items-start px-3" : "items-center",
              )}
            >
              <SidebarBody
                expanded={sidebarExpanded}
                pathname={location.pathname}
                searchRole={searchRole}
                ingestFresh={ingestFresh}
                navItems={visibleNavItems}
                displayName={sidebarDisplay.name}
                subtitle={sidebarDisplay.subtitle}
                avatarUrl={sidebarDisplay.avatarUrl}
                onLogout={handleLogout}
              />
            </aside>
          </div>

          {/* Mobile overlay backdrop */}
          <div
            className={cn(
              "fixed inset-0 z-40 bg-black/50 transition-opacity duration-300 md:hidden",
              sidebarExpanded ? "opacity-100" : "pointer-events-none opacity-0",
            )}
            onClick={() => setSidebarExpanded(false)}
            aria-hidden="true"
          />

          {/* Mobile sidebar — fixed, slides in/out */}
          <div
            className={cn(
              "fixed inset-y-0 left-0 z-50 flex w-[248px] flex-col transition-transform duration-300 ease-out md:hidden",
              sidebarExpanded ? "translate-x-0" : "-translate-x-full",
            )}
            aria-hidden={!sidebarExpanded}
          >
            <aside className={cn(SIDEBAR_ASIDE_CLASSES, "items-start px-3")}>
              <SidebarBody
                expanded
                pathname={location.pathname}
                searchRole={searchRole}
                ingestFresh={ingestFresh}
                navItems={visibleNavItems}
                displayName={sidebarDisplay.name}
                subtitle={sidebarDisplay.subtitle}
                avatarUrl={sidebarDisplay.avatarUrl}
                onNavigate={closeMobileSidebar}
                onLogout={handleLogout}
              />
            </aside>
          </div>

          <main className="scrollbar-hidden z-10 min-h-0 min-w-0 flex-1 overflow-y-auto bg-white p-3 sm:p-4 md:p-5">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
