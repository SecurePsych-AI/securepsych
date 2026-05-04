import { Zap, Microscope } from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  value: "fast" | "deep";
  onChange: (m: "fast" | "deep") => void;
}

export function ModeToggle({ value, onChange }: Props) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-md bg-secondary p-0.5 text-[12px]">
      <button
        type="button"
        onClick={() => onChange("fast")}
        className={cn(
          "inline-flex h-6 items-center gap-1 rounded-sm px-2 transition-colors",
          value === "fast"
            ? "bg-background text-foreground shadow-seg-active"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <Zap className="h-3 w-3" />
        Fast
      </button>
      <button
        type="button"
        onClick={() => onChange("deep")}
        className={cn(
          "inline-flex h-6 items-center gap-1 rounded-sm px-2 transition-colors",
          value === "deep"
            ? "bg-background text-foreground shadow-seg-active"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <Microscope className="h-3 w-3" />
        Deep
      </button>
    </div>
  );
}
