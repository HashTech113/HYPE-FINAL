import { createFileRoute, redirect } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Bell, Settings, AlertTriangle, Info, AlertOctagon } from "lucide-react";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { mockAlerts, alertRules } from "@/data/mockAlerts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { formatDateTime } from "@/lib/dateFormat";
import { getCurrentRole } from "@/lib/auth";

export const Route = createFileRoute("/_dashboard/alerts")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: AlertsPage,
});

function AlertsPage() {
  const [rules, setRules] = useState(alertRules);

  const formattedAlerts = useMemo(
    () =>
      mockAlerts.map((alert) => ({
        ...alert,
        formattedTimestamp: formatDateTime(alert.timestamp),
      })),
    []
  );

  const alertCounts = useMemo(() => {
    return mockAlerts.reduce(
      (counts, alert) => {
        counts.total += 1;
        counts[alert.type] += 1;
        return counts;
      },
      { total: 0, critical: 0, warning: 0, info: 0 }
    );
  }, []);

  return (
    <div className="flex min-h-full flex-col">
      <SectionShell title="Alerts & Automation" icon={<Bell className="h-5 w-5 text-primary" />}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 animate-fade-in-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Bell className="h-4 w-4 text-primary" />Real-time Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative space-y-4">
              <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
              {formattedAlerts.map((alert) => (
                <div key={alert.id} className="relative flex items-start gap-4 pl-10">
                  <div
                    className={cn(
                      "absolute left-2.5 top-1 h-3 w-3 rounded-full border-2 border-card",
                      alert.type === "critical" ? "bg-destructive" : alert.type === "warning" ? "bg-warning" : "bg-primary"
                    )}
                  />
                  <div className="flex-1 rounded-lg border border-border p-3">
                    <div className="flex items-center gap-2">
                      {alert.type === "critical" ? (
                        <AlertOctagon className="h-4 w-4 text-destructive" />
                      ) : alert.type === "warning" ? (
                        <AlertTriangle className="h-4 w-4 text-warning-foreground" />
                      ) : (
                        <Info className="h-4 w-4 text-primary" />
                      )}
                      <span className="text-sm font-semibold">{alert.title}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{alert.description}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                      {alert.employee && <span>Employee: {alert.employee}</span>}
                      <span>|</span>
                      <span>{alert.formattedTimestamp}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="animate-fade-in-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Settings className="h-4 w-4 text-muted-foreground" />Rule Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Late Threshold (minutes)</Label>
              <Input
                type="number"
                value={rules.lateThreshold}
                onChange={(e) => setRules({ ...rules, lateThreshold: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Early Exit Threshold (minutes)</Label>
              <Input
                type="number"
                value={rules.earlyExitThreshold}
                onChange={(e) => setRules({ ...rules, earlyExitThreshold: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Multiple Exits Threshold</Label>
              <Input
                type="number"
                value={rules.multipleExitsThreshold}
                onChange={(e) => setRules({ ...rules, multipleExitsThreshold: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>After-Hours Start</Label>
              <Input
                type="time"
                value={rules.afterHoursStart}
                onChange={(e) => setRules({ ...rules, afterHoursStart: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>After-Hours End</Label>
              <Input
                type="time"
                value={rules.afterHoursEnd}
                onChange={(e) => setRules({ ...rules, afterHoursEnd: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card className="animate-fade-in-up">
          <CardHeader>
            <CardTitle className="text-base">Daily Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Alerts</span>
                <span className="font-semibold">{alertCounts.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Critical</span>
                <span className="font-semibold text-destructive">{alertCounts.critical}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Warnings</span>
                <span className="font-semibold text-warning-foreground">{alertCounts.warning}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Info</span>
                <span className="font-semibold text-primary">{alertCounts.info}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="animate-fade-in-up">
          <CardHeader>
            <CardTitle className="text-base">Weekly Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mon</span>
                <span>3 alerts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tue</span>
                <span>5 alerts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Wed</span>
                <span>2 alerts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Thu</span>
                <span>7 alerts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Fri</span>
                <span>4 alerts</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </SectionShell>
    </div>
  );
}
