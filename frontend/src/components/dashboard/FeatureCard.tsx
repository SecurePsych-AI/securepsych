import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";

import { cn } from "@/lib/utils";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  href: string;
  disabled?: boolean;
  comingSoon?: boolean;
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  disabled,
  comingSoon,
}: FeatureCardProps) {
  const inner = (
    <div
      className={cn(
        "group flex h-full flex-col gap-3 rounded-xl border border-border bg-card p-5 transition-all",
        !disabled && "hover:border-border-strong hover:bg-secondary/50",
        disabled && "opacity-60",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft text-primary">
          <Icon className="h-4 w-4" />
        </div>
        {comingSoon && (
          <span className="trust-pill-warning">Coming soon</span>
        )}
      </div>
      <div className="space-y-1">
        <h3 className="text-[14.5px] font-semibold tracking-tight">{title}</h3>
        <p className="text-[13px] leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>
      {!disabled && (
        <span className="mt-auto inline-flex items-center gap-1 text-[12.5px] font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
          Open <ArrowRight className="h-3 w-3" />
        </span>
      )}
    </div>
  );

  if (disabled) return <div>{inner}</div>;
  return (
    <Link to={href} className="block focus-ring rounded-xl">
      {inner}
    </Link>
  );
}
