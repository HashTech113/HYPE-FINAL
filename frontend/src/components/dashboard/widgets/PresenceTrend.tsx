import { useMemo, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { TrendingDown, TrendingUp, Minus, LineChart as LineIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import { buildPresenceSeries, type PresenceTimeframe } from "@/lib/dashboardData";
import { cn } from "@/lib/utils";

export function PresenceTrend() {
  const { attendance } = useDashboardData();
  const [timeframe, setTimeframe] = useState<PresenceTimeframe>("daily");

  const series = useMemo(() => buildPresenceSeries(attendance, timeframe), [attendance, timeframe]);

  const delta = series.deltaPct;
  const deltaIsUp = delta > 0;
  const deltaIsDown = delta < 0;

  return (
    <Card className="dashboard-chart flex h-full flex-col">
      <CardHeader className="flex flex-row items-start justify-between gap-3 pb-2 pl-0">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <LineIcon className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold">Presence Trend</CardTitle>
            <p className="text-xs text-muted-foreground">
              {timeframe === "daily" ? "Last 7 days" : "Last 4 weeks"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold transition-colors",
              deltaIsUp && "bg-emerald-50 text-emerald-700",
              deltaIsDown && "bg-rose-50 text-rose-700",
              !deltaIsUp && !deltaIsDown && "bg-slate-100 text-slate-600",
            )}
            title="Change vs previous period"
          >
            {deltaIsUp ? (
              <TrendingUp className="h-3.5 w-3.5" />
            ) : deltaIsDown ? (
              <TrendingDown className="h-3.5 w-3.5" />
            ) : (
              <Minus className="h-3.5 w-3.5" />
            )}
            {delta > 0 ? "+" : ""}
            {delta}%
          </span>

          <div className="flex rounded-md border border-slate-200 bg-white p-0.5 text-xs font-medium">
            <button
              type="button"
              onClick={() => setTimeframe("daily")}
              className={cn(
                "rounded px-2.5 py-1 transition-colors",
                timeframe === "daily"
                  ? "bg-primary text-primary-foreground"
                  : "text-slate-600 hover:bg-slate-100",
              )}
            >
              Daily
            </button>
            <button
              type="button"
              onClick={() => setTimeframe("weekly")}
              className={cn(
                "rounded px-2.5 py-1 transition-colors",
                timeframe === "weekly"
                  ? "bg-primary text-primary-foreground"
                  : "text-slate-600 hover:bg-slate-100",
              )}
            >
              Weekly
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col gap-3 pb-2">
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-semibold tabular-nums">{series.currentAvg}%</span>
          <span className="text-xs text-muted-foreground">avg attendance</span>
        </div>

        <div className="min-h-0 flex-1 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={series.points}
              margin={{ top: 8, right: 12, left: -12, bottom: 0 }}
              key={timeframe /* force remount on toggle so the draw anim replays */}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                formatter={(v: number) => [`${v}%`, "Presence"]}
                labelClassName="text-xs"
                contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0" }}
              />
              <Line
                type="monotone"
                dataKey="presentRate"
                stroke="#0f9f7f"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#0f9f7f" }}
                activeDot={{ r: 5 }}
                animationDuration={1200}
                isAnimationActive
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
