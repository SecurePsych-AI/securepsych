import { Link, useLocation } from "react-router-dom";
import { Folder, MessageSquare, FileText, Languages, History } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface Tool {
  key: "overview" | "qa" | "summarize" | "jargon" | "history";
  label: string;
  icon: LucideIcon;
  segment: string;
}

const TOOLS: Tool[] = [
  { key: "overview", label: "Overview", icon: Folder, segment: "" },
  { key: "qa", label: "Q&A", icon: MessageSquare, segment: "qa" },
  { key: "summarize", label: "Summarize", icon: FileText, segment: "summarize" },
  { key: "jargon", label: "Simplify", icon: Languages, segment: "jargon" },
  { key: "history", label: "History", icon: History, segment: "history" },
];

interface Props {
  projectId: string;
}

export function ToolSwitcher({ projectId }: Props) {
  const { pathname } = useLocation();
  const base = `/p/${projectId}`;
  const sub = pathname.startsWith(base + "/")
    ? pathname.slice((base + "/").length).split("/")[0]
    : "";

  return (
    <div className="inline-flex items-center gap-0.5 rounded-lg bg-secondary p-1">
      {TOOLS.map((t) => {
        const active = (t.segment === "" && sub === "") || sub === t.segment;
        const href = t.segment === "" ? base : `${base}/${t.segment}`;
        return (
          <Link
            key={t.key}
            to={href}
            title={t.label}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-[12.5px] font-medium transition-colors",
              active
                ? "bg-background text-foreground shadow-seg-active"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <t.icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{t.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
