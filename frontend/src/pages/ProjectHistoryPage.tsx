import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Download, MessageSquare, FileText, Languages, ArrowRight } from "lucide-react";

import { TopBar } from "@/components/layout/TopBar";
import { ToolSwitcher } from "@/components/layout/ToolSwitcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  useProject,
  useProjectThreads,
  useProjectSummaries,
  useProjectJargonRuns,
} from "@/hooks/use-projects";
import { useSelectionStore } from "@/store/selection";
import { relativeTime } from "@/lib/format";

type FilterKey = "all" | "qa" | "summary" | "jargon";

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "All" },
  { key: "qa", label: "Q&A" },
  { key: "summary", label: "Summaries" },
  { key: "jargon", label: "Jargon" },
];

interface Row {
  kind: Exclude<FilterKey, "all">;
  title: string;
  excerpt: string;
  href: string;
  ts: string;
  meta: string;
}

export default function ProjectHistoryPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const { data: project } = useProject(projectId);
  const threads = useProjectThreads(projectId);
  const summaries = useProjectSummaries(projectId);
  const jargon = useProjectJargonRuns(projectId);
  const [filter, setFilter] = useState<FilterKey>("all");

  useEffect(() => {
    if (projectId) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    for (const t of threads.data ?? []) {
      out.push({
        kind: "qa",
        title: t.title ?? "Q&A thread",
        excerpt: "Threaded conversation with citations.",
        href: `/p/${projectId}/qa/${t.id}`,
        ts: t.created_at,
        meta: "Q&A",
      });
    }
    for (const s of summaries.data ?? []) {
      const firstLine = s.summary.split("\n").find(Boolean) ?? "";
      out.push({
        kind: "summary",
        title: s.filename_redacted,
        excerpt: firstLine.slice(0, 200),
        href: `/p/${projectId}/summarize`,
        ts: s.created_at,
        meta: `${s.page_count} pages`,
      });
    }
    for (const j of jargon.data ?? []) {
      out.push({
        kind: "jargon",
        title: `Simplified at Level ${j.level}`,
        excerpt: j.input_preview,
        href: `/p/${projectId}/jargon`,
        ts: j.created_at,
        meta: `FK ${j.fk_grade.toFixed(1)}`,
      });
    }
    out.sort((a, b) => (a.ts < b.ts ? 1 : -1));
    return out;
  }, [projectId, threads.data, summaries.data, jargon.data]);

  const visible = filter === "all" ? rows : rows.filter((r) => r.kind === filter);

  const onExport = () => {
    const blob = new Blob([JSON.stringify({ project: project?.display_label, rows: visible }, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `history_${project?.display_label?.replace(/\s+/g, "_") ?? "project"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!projectId) return null;

  return (
    <>
      <TopBar
        breadcrumbs={[
          { label: "SecurePsych AI", to: "/" },
          { label: project?.display_label ?? "Project", to: `/p/${projectId}` },
          { label: "History" },
        ]}
        rightSlot={<ToolSwitcher projectId={projectId} />}
      />
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-5xl space-y-5">
          <header className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <h1 className="text-[19px] font-semibold tracking-tight">Activity history</h1>
              <p className="text-[13px] text-muted-foreground">
                Every thread, summary, and jargon run for this project.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center gap-0.5 rounded-md bg-secondary p-0.5">
                {FILTERS.map((f) => (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => setFilter(f.key)}
                    className={cn(
                      "h-7 rounded-sm px-2.5 text-[12.5px] font-medium transition-colors",
                      filter === f.key
                        ? "bg-background text-foreground shadow-seg-active"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
              <Button type="button" variant="outline" size="sm" onClick={onExport}>
                <Download className="h-3.5 w-3.5" />
                Export JSON
              </Button>
            </div>
          </header>

          {visible.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-[13px] text-muted-foreground">
                  No activity in this filter yet.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {visible.map((r, i) => (
                <Card key={`${r.href}-${i}`} className="transition-colors hover:bg-secondary/40">
                  <CardContent className="space-y-2 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <Badge
                        variant={
                          r.kind === "qa"
                            ? "accent"
                            : r.kind === "summary"
                              ? "default"
                              : "warning"
                        }
                      >
                        {r.kind === "qa" && <MessageSquare className="h-3 w-3" />}
                        {r.kind === "summary" && <FileText className="h-3 w-3" />}
                        {r.kind === "jargon" && <Languages className="h-3 w-3" />}
                        {r.kind === "qa" ? "Q&A" : r.kind === "summary" ? "Summary" : "Jargon"}
                      </Badge>
                      <span className="text-[11.5px] text-muted-foreground">
                        {relativeTime(r.ts)}
                      </span>
                    </div>
                    <h3 className="text-[14px] font-semibold tracking-tight">
                      {r.title}
                    </h3>
                    <p className="line-clamp-2 text-[13px] leading-[1.55] text-muted-foreground">
                      {r.excerpt}
                    </p>
                    <div className="flex items-center justify-between border-t border-border pt-2">
                      <span className="text-[11.5px] text-muted-foreground">{r.meta}</span>
                      <Button asChild variant="ghost" size="sm">
                        <Link to={r.href}>
                          Open <ArrowRight className="h-3 w-3" />
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
