interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  icon?: React.ReactNode;
  /** When true, ``actions`` render inline with the title instead of being
   * pushed to the far right by ``justify-between``. Useful when the action
   * is conceptually scoped to the section (e.g., a search/filter for this
   * page) and reads better adjacent to the heading. */
  inlineActions?: boolean;
}

export function PageHeader({
  title,
  description,
  actions,
  icon,
  inlineActions = false,
}: PageHeaderProps) {
  return (
    <div className="sticky top-0 z-20 flex flex-col gap-1 bg-transparent pb-2 sm:flex-row sm:items-center sm:justify-between">
      <div
        className={
          inlineActions
            ? "flex w-full flex-1 flex-col items-stretch gap-3 sm:flex-row sm:flex-wrap sm:items-center"
            : undefined
        }
      >
        <h1 className="flex items-center gap-2 text-2xl font-extrabold tracking-tight text-foreground">
          {icon}
          <span>{title}</span>
        </h1>
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
        {inlineActions && actions ? (
          // flex-1 lets the inline actions container fill the title row, so
          // children using ``ml-auto`` (e.g., a Refresh button) can push to
          // the far-right edge. flex-wrap keeps mobile layouts from squashing
          // multi-control headers — children flow onto a second row when the
          // viewport is too narrow to fit them inline.
          <div className="flex flex-1 flex-wrap items-center gap-2">{actions}</div>
        ) : null}
      </div>
      {!inlineActions && actions && (
        <div className="flex items-center gap-2 mt-2 sm:mt-0">{actions}</div>
      )}
    </div>
  );
}
