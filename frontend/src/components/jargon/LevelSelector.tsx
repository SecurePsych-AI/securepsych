import { cn } from "@/lib/utils";
import type { JargonLevel } from "@/types/api";

const LEVELS: { value: JargonLevel; label: string; sub: string }[] = [
  { value: 1, label: "L1", sub: "Psychologist" },
  { value: 2, label: "L2", sub: "Educator" },
  { value: 3, label: "L3", sub: "Parent" },
  { value: 4, label: "L4", sub: "High school" },
  { value: 5, label: "L5", sub: "Elementary" },
];

interface Props {
  value: JargonLevel;
  onChange: (level: JargonLevel) => void;
  disabled?: boolean;
}

export function LevelSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="grid grid-cols-5 gap-2">
      {LEVELS.map((l) => {
        const active = value === l.value;
        return (
          <button
            key={l.value}
            type="button"
            onClick={() => onChange(l.value)}
            disabled={disabled}
            className={cn(
              "flex flex-col items-center justify-center gap-0.5 rounded-md border px-2 py-2 text-[12.5px] transition-colors",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground hover:bg-secondary",
              disabled && "opacity-50 pointer-events-none",
            )}
          >
            <span className="font-semibold">{l.label}</span>
            <span className={cn("text-[11px]", active ? "text-primary-foreground/80" : "text-muted-foreground")}>
              {l.sub}
            </span>
          </button>
        );
      })}
    </div>
  );
}
