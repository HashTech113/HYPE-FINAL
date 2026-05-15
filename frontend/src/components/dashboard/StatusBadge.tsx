import { cn } from "@/lib/utils";

const statusStyles: Record<string, string> = {
  Active: "bg-success/10 text-success",
  Present: "bg-success/10 text-success",
  Online: "bg-success/10 text-success",
  Approved: "bg-success/10 text-success",
  Inactive: "bg-muted text-muted-foreground",
  Absent: "bg-muted text-muted-foreground",
  Offline: "bg-destructive/10 text-destructive",
  Denied: "bg-destructive/10 text-destructive",
  Late: "bg-warning/10 text-warning-foreground",
  "Early Exit": "bg-warning/10 text-warning-foreground",
  Pending: "bg-primary/10 text-primary",
  "On Leave": "bg-primary/10 text-primary",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn(
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
      statusStyles[status] ?? "bg-muted text-muted-foreground"
    )}>
      {status}
    </span>
  );
}
