import { useMemo, type ReactNode } from "react";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import { buildTopAlerts, type AlertSeverity } from "@/lib/dashboardData";
import { cn } from "@/lib/utils";

const SEVERITY_STYLES: Record<AlertSeverity, { icon: ReactNode; row: string; badge: string }> = {
  critical: {
    icon: <AlertCircle className="h-4 w-4 text-rose-600" />,
    row: "border-rose-200 bg-rose-50/50",
    badge: "bg-rose-100 text-rose-700",
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4 text-amber-600" />,
    row: "border-amber-200 bg-amber-50/50",
    badge: "bg-amber-100 text-amber-700",
  },
  info: {
    icon: <Info className="h-4 w-4 text-sky-600" />,
    row: "border-sky-200 bg-sky-50/50",
    badge: "bg-sky-100 text-sky-700",
  },
};

export function TopAlerts() {
  const { attendance } = useDashboardData();
  const alerts = useMemo(() => buildTopAlerts(attendance), [attendance]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center gap-2 pb-2 pl-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <CardTitle className="text-base font-semibold">Top 3 Alerts Today</CardTitle>
          <p className="text-xs text-muted-foreground">Anomalies requiring attention</p>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-2.5">
        {alerts.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            No anomalies. Nice and quiet.
          </p>
        ) : (
          alerts.map((a) => {
            const style = SEVERITY_STYLES[a.severity];
            return (
              <div
                key={a.id}
                className={cn(
                  "flex items-start gap-3 rounded-lg border p-3 transition hover:-translate-y-0.5 hover:shadow-sm",
                  style.row,
                )}
              >
                <div className="mt-0.5">{style.icon}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold text-foreground">
                      {a.name}
                    </span>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                        style.badge,
                      )}
                    >
                      {a.type}
                    </span>
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-slate-600">{a.subtitle}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {a.company} · {a.date}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
