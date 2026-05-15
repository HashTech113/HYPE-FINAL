import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { getCurrentRole } from "@/lib/auth";

// Layout route for /cameras and /cameras/live. The actual pages live in
// _dashboard.cameras.index.tsx (Add Camera) and _dashboard.cameras.live.tsx
// (Live Cameras). Without this layout file, TanStack would treat
// _dashboard.cameras as the parent of _dashboard.cameras.live and render
// the parent component (Add Camera) at /cameras/live, since the parent
// wouldn't include an <Outlet />.
export const Route = createFileRoute("/_dashboard/cameras")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: CamerasLayout,
});

function CamerasLayout() {
  return <Outlet />;
}
