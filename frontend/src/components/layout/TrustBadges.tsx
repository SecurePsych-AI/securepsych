import { ShieldCheck, Server, WifiOff } from "lucide-react";

import { cn } from "@/lib/utils";

interface TrustBadgesProps {
  className?: string;
  size?: "sm" | "md";
}

export function TrustBadges({ className, size = "sm" }: TrustBadgesProps) {
  const iconSize = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5";
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      <span className="trust-pill-success">
        <ShieldCheck className={iconSize} />
        FERPA-compliant
      </span>
      <span className="trust-pill-accent">
        <Server className={iconSize} />
        On-prem
      </span>
      <span className="trust-pill-success">
        <WifiOff className={iconSize} />
        Air-gapped
      </span>
    </div>
  );
}
