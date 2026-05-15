import { createFileRoute, redirect } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Loader2, RefreshCw, UserX } from "lucide-react";

import { SectionShell } from "@/components/dashboard/SectionShell";
import { ClusterDetailDialog } from "@/components/unknowns/ClusterDetailDialog";
import { ClusterGrid } from "@/components/unknowns/ClusterGrid";
import { PromoteNewDialog } from "@/components/unknowns/PromoteNewDialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getCurrentRole } from "@/lib/auth";
import {
  usePromoteToNewEmployee,
  useUnknownClusterList,
} from "@/lib/hooks/useUnknowns";

export const Route = createFileRoute("/_dashboard/unknown-faces")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: UnknownFacesPage,
});

const PAGE_SIZE = 24;

function UnknownFacesPage() {
  // Header filters were removed at request time — the page is now scoped
  // exclusively to pending-review clusters. Promoted / merged / ignored
  // clusters are still accessible via the API for future tooling but
  // aren't shown here to keep the operator focused on un-triaged faces.
  const [page, setPage] = useState(0);
  const [detailClusterId, setDetailClusterId] = useState<number | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [promoteOpen, setPromoteOpen] = useState(false);
  const [promoteClusterId, setPromoteClusterId] = useState<number | null>(null);

  const listQuery = useUnknownClusterList({
    status: "PENDING",
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });

  const promoteNew = usePromoteToNewEmployee();

  const total = listQuery.data?.total ?? 0;
  const clusters = useMemo(() => listQuery.data?.items ?? [], [listQuery.data?.items]);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const errorMsg = listQuery.error instanceof Error ? listQuery.error.message : null;

  function openDetail(clusterId: number) {
    setDetailClusterId(clusterId);
    setDetailOpen(true);
  }

  function handlePromoteNewRequest(clusterId: number) {
    setPromoteClusterId(clusterId);
    setPromoteOpen(true);
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Unknown Faces"
        icon={<UserX className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        actions={
          <div className="flex items-center gap-3 md:gap-4">
            <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
              </span>
              <span className="tabular-nums">
                {total} unknown image{total === 1 ? "" : "s"}
              </span>
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-10 gap-1.5 px-4"
              onClick={() => listQuery.refetch()}
              disabled={listQuery.isFetching}
              title="Refresh"
            >
              <RefreshCw className={cn("h-4 w-4", listQuery.isFetching && "animate-spin")} />
              {listQuery.isFetching ? "Refreshing…" : "Refresh"}
            </Button>
          </div>
        }
      >
        <Card className="flex min-h-0 flex-1 flex-col">
          <CardContent className="flex min-h-0 flex-1 flex-col gap-3 pt-4">
            {errorMsg && (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {errorMsg}
              </div>
            )}

            <div className="show-scrollbar min-h-0 flex-1 overflow-y-auto">
              {listQuery.isLoading && clusters.length === 0 ? (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading…
                </div>
              ) : (
                <ClusterGrid clusters={clusters} loading={listQuery.isLoading} onOpen={openDetail} />
              )}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
                <span>
                  Page {page + 1} of {totalPages}
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={page === 0}
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </SectionShell>

      <ClusterDetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        clusterId={detailClusterId}
        onPromoteNew={handlePromoteNewRequest}
      />

      <PromoteNewDialog
        open={promoteOpen}
        onOpenChange={(next) => {
          setPromoteOpen(next);
          if (!next) setPromoteClusterId(null);
        }}
        clusterId={promoteClusterId}
        submitting={promoteNew.isPending}
        onSubmit={(payload) => {
          if (promoteClusterId === null) return;
          promoteNew.mutate(
            { clusterId: promoteClusterId, payload },
            {
              onSuccess: () => {
                setPromoteOpen(false);
                setPromoteClusterId(null);
              },
            },
          );
        }}
      />
    </div>
  );
}
