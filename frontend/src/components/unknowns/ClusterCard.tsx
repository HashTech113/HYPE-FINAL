import { UserX } from "lucide-react";

import type { UnknownCluster, UnknownClusterStatus } from "@/lib/types/unknowns";
import { UnknownFaceImage } from "./UnknownFaceImage";
import { cn } from "@/lib/utils";
import { formatDateDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";

const STATUS_STYLES: Record<UnknownClusterStatus, string> = {
  PENDING: "bg-amber-500/90 text-white",
  PROMOTED: "bg-emerald-500/90 text-white",
  IGNORED: "bg-slate-500/90 text-white",
  MERGED: "bg-sky-500/90 text-white",
};

type Props = {
  cluster: UnknownCluster;
  onOpen: (clusterId: number) => void;
};

export function ClusterCard({ cluster, onOpen }: Props) {
  const lastSeen = parseTimestamp(cluster.last_seen_at);
  const title = cluster.label?.trim() || `Unknown #${cluster.id}`;
  return (
    // The button itself is the aspect-locked container — ``aspect-[3/4]``
    // gives every card identical proportions in the grid, regardless of
    // label length or face-count badge width. The image becomes
    // ``flex-1`` and stretches to whatever space remains after the
    // footer, so all images line up at the same Y coordinate.
    <button
      type="button"
      onClick={() => onOpen(cluster.id)}
      className={cn(
        "group flex aspect-[3/4] w-full flex-col overflow-hidden rounded-xl border border-rose-200/60 bg-slate-900 text-left shadow-sm transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-rose-400",
      )}
    >
      <div className="relative min-h-0 flex-1 w-full">
        <UnknownFaceImage captureId={cluster.representative_capture_id} alt={title} />
        <span
          className={cn(
            "absolute left-2 top-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide shadow",
            STATUS_STYLES[cluster.status],
          )}
        >
          <UserX className="h-3 w-3" />
          {cluster.status.toLowerCase()}
        </span>
        <span className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[10px] font-semibold text-white">
          {cluster.member_count} face{cluster.member_count === 1 ? "" : "s"}
        </span>
      </div>
      <div className="flex shrink-0 flex-col gap-1 bg-slate-950/90 px-3 py-2">
        <div className="truncate text-sm font-semibold text-rose-50" title={title}>
          {title}
        </div>
        <div className="flex items-center justify-between gap-2 text-[11px] tabular-nums text-rose-200/80">
          <span className="truncate">
            {lastSeen ? formatDateDash(lastSeen) : "—"}
          </span>
          <span className="truncate">
            {lastSeen ? formatTime12(lastSeen) : ""}
          </span>
        </div>
      </div>
    </button>
  );
}
