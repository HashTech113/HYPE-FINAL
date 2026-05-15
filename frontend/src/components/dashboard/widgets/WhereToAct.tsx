import { useMemo } from "react";
import { Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import { buildActionItems, type ActionPriority, type PatternType } from "@/lib/dashboardData";
import { cn } from "@/lib/utils";

const PRIORITY_STYLES: Record<ActionPriority, string> = {
  High: "bg-rose-100 text-rose-700",
  Medium: "bg-amber-100 text-amber-700",
};

const TYPE_LABEL: Record<PatternType, string> = {
  late: "Late arrivals",
  early: "Early exits",
  absence: "Absenteeism",
  missed: "Missed checkouts",
};

export function WhereToAct() {
  const { attendance } = useDashboardData();
  const items = useMemo(() => buildActionItems(attendance), [attendance]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Target className="h-5 w-5" />
        </div>
        <div>
          <CardTitle className="text-base font-semibold">Where To Act</CardTitle>
          <p className="text-xs text-muted-foreground">
            Teams that need the most attention, with the dominant issue
          </p>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col">
        {items.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            All teams are performing well. No immediate action needed.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {items.map((item) => (
              <div
                key={item.company}
                className="neu-surface neu-surface-hover flex flex-col gap-2 rounded-2xl border-0 p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-foreground">
                      {item.company}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Score {item.score} · {TYPE_LABEL[item.issueType]} {Math.round(item.issueRate * 100)}%
                    </div>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                      PRIORITY_STYLES[item.priority],
                    )}
                  >
                    {item.priority}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600">{item.recommendation}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
