import { useMemo } from "react";
import { ArrowDownRight, ArrowUpRight, Minus, Repeat } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import { buildRepeatPatterns, type PatternType } from "@/lib/dashboardData";
import { cn } from "@/lib/utils";

const TYPE_LABEL: Record<PatternType, string> = {
  late: "Late arrivals",
  early: "Early exits",
  absence: "Absences",
  missed: "Missed checkout",
};

const TYPE_BADGE: Record<PatternType, string> = {
  late: "bg-amber-100 text-amber-700 hover:bg-amber-200",
  early: "bg-orange-100 text-orange-700 hover:bg-orange-200",
  absence: "bg-rose-100 text-rose-700 hover:bg-rose-200",
  missed: "bg-sky-100 text-sky-700 hover:bg-sky-200",
};

export function RepeatPatterns() {
  const { attendance } = useDashboardData();
  const rows = useMemo(() => buildRepeatPatterns(attendance), [attendance]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center gap-2 pb-2 pl-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
          <Repeat className="h-5 w-5" />
        </div>
        <div>
          <CardTitle className="text-base font-semibold">Top 5 Repeat Patterns</CardTitle>
          <p className="text-xs text-muted-foreground">14-day window — last 7 vs prior 7</p>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col">
        {rows.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">No repeat patterns.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {rows.map((p) => {
              const TrendIcon = p.trend === "up" ? ArrowUpRight : p.trend === "down" ? ArrowDownRight : Minus;
              const trendColor =
                p.trend === "up"
                  ? "text-rose-600"
                  : p.trend === "down"
                    ? "text-emerald-600"
                    : "text-slate-500";
              return (
                <div
                  key={p.name}
                  className="flex items-center justify-between gap-3 py-2.5 transition-colors hover:bg-slate-50/60"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-foreground">{p.name}</div>
                    <div className="text-[11px] text-slate-500">{p.company}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition-colors",
                        TYPE_BADGE[p.dominantType],
                      )}
                    >
                      {TYPE_LABEL[p.dominantType]}
                    </span>
                    <span className="min-w-[2ch] text-right text-sm font-semibold tabular-nums text-foreground">
                      {p.total14}
                    </span>
                    <span
                      className={cn(
                        "inline-flex items-center gap-0.5 text-xs font-medium",
                        trendColor,
                      )}
                      title={`Last 7d: ${p.occurrencesLast7}  •  Prev 7d: ${p.occurrencesPrev7}`}
                    >
                      <TrendIcon className="h-3.5 w-3.5" />
                      {p.occurrencesLast7 - p.occurrencesPrev7 > 0 ? "+" : ""}
                      {p.occurrencesLast7 - p.occurrencesPrev7}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
