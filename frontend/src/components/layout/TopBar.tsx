import { useLocation, Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useFeatureFlags } from "@/hooks/use-feature-flags";

interface TopBarProps {
  className?: string;
  rightSlot?: React.ReactNode;
  breadcrumbs?: { label: string; to?: string }[];
}

export function TopBar({ className, rightSlot, breadcrumbs }: TopBarProps) {
  const { data: flags, isError } = useFeatureFlags();
  const location = useLocation();
  const crumbs = breadcrumbs ?? defaultCrumbs(location.pathname);

  return (
    <header
      className={cn(
        "flex h-12 items-center justify-between gap-4 border-b border-border bg-background px-6",
        className,
      )}
    >
      <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground">
        {crumbs.map((c, i) => (
          <span key={`${c.label}-${i}`} className="flex items-center gap-1.5">
            {i > 0 && <span className="text-muted-foreground/60">/</span>}
            {c.to ? (
              <Link
                to={c.to}
                className="rounded-sm px-1 transition-colors hover:bg-secondary hover:text-foreground"
              >
                {c.label}
              </Link>
            ) : (
              <span className={i === crumbs.length - 1 ? "text-foreground" : ""}>
                {c.label}
              </span>
            )}
          </span>
        ))}
      </nav>

      <div className="flex items-center gap-3">
        {rightSlot}
        {flags ? (
          <Badge variant="success" title="Backend reachable">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            Operational
          </Badge>
        ) : isError ? (
          <Badge variant="warning" title="Backend unreachable">
            <span className="h-1.5 w-1.5 rounded-full bg-warning" />
            Mock mode
          </Badge>
        ) : (
          <Badge variant="default">
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
            Connecting…
          </Badge>
        )}
      </div>
    </header>
  );
}

function defaultCrumbs(pathname: string): { label: string; to?: string }[] {
  if (pathname === "/" || pathname === "/login") return [{ label: "SecurePsych AI" }];
  return [{ label: "SecurePsych AI", to: "/" }, { label: pathname }];
}
