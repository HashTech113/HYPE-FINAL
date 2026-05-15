import * as React from "react";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type SectionShellProps = {
  title: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  /** Render actions inline with the title (next to it) instead of pushing
   * them to the far right of the header row. */
  inlineActions?: boolean;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
};

export function SectionShell({
  title,
  icon,
  actions,
  inlineActions,
  children,
  className,
  contentClassName,
}: SectionShellProps) {
  return (
    <Card
      className={cn(
        "mx-2 my-2 flex min-h-0 flex-1 flex-col overflow-hidden !rounded-3xl !border !border-slate-200",
        className,
      )}
    >
      <CardContent className={cn("flex min-h-0 flex-1 flex-col gap-4 p-4", contentClassName)}>
        <PageHeader title={title} icon={icon} actions={actions} inlineActions={inlineActions} />
        {children}
      </CardContent>
    </Card>
  );
}
