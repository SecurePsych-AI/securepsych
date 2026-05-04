import { Link } from "react-router-dom";
import { MessageSquare, FileText, Languages, ChevronRight } from "lucide-react";

import {
  useProjects,
  useProjectThreads,
  useProjectSummaries,
  useProjectJargonRuns,
} from "@/hooks/use-projects";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { relativeTime } from "@/lib/format";
import type { Project } from "@/types/api";

interface Row {
  kind: "qa" | "summary" | "jargon";
  title: string;
  excerpt?: string;
  href: string;
  projectLabel: string;
  ts: string;
}

const KIND_LABEL: Record<Row["kind"], string> = {
  qa: "Q&A",
  summary: "Summary",
  jargon: "Jargon",
};

function KindIcon({ kind }: { kind: Row["kind"] }) {
  const Icon =
    kind === "qa" ? MessageSquare : kind === "summary" ? FileText : Languages;
  return <Icon className="h-3.5 w-3.5" />;
}

function useRecentRows(project: Project | undefined): Row[] {
  const projectId = project?.id;
  const threads = useProjectThreads(projectId);
  const summaries = useProjectSummaries(projectId);
  const jargon = useProjectJargonRuns(projectId);

  if (!project) return [];

  const rows: Row[] = [];
  for (const t of threads.data ?? []) {
    rows.push({
      kind: "qa",
      title: t.title ?? "Q&A thread",
      href: `/p/${project.id}/qa/${t.id}`,
      projectLabel: project.display_label,
      ts: t.created_at,
    });
  }
  for (const s of summaries.data ?? []) {
    rows.push({
      kind: "summary",
      title: `Summary · ${s.filename_redacted}`,
      excerpt: s.summary.split("\n").find(Boolean)?.slice(0, 120),
      href: `/p/${project.id}/summarize`,
      projectLabel: project.display_label,
      ts: s.created_at,
    });
  }
  for (const j of jargon.data ?? []) {
    rows.push({
      kind: "jargon",
      title: `Simplified at Level ${j.level}`,
      excerpt: j.input_preview,
      href: `/p/${project.id}/jargon`,
      projectLabel: project.display_label,
      ts: j.created_at,
    });
  }
  rows.sort((a, b) => (a.ts < b.ts ? 1 : -1));
  return rows;
}

interface Props {
  limit?: number;
}

export function RecentActivityList({ limit = 5 }: Props) {
  const { data: projects = [] } = useProjects();
  const project = projects[0];
  const rows = useRecentRows(project).slice(0, limit);

  if (!project) {
    return (
      <p className="text-sm text-muted-foreground">
        Create your first project to begin.
      </p>
    );
  }

  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Activity from your projects will appear here.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-border rounded-xl border border-border bg-card">
      {rows.map((r, i) => (
        <li key={`${r.href}-${i}`}>
          <Link
            to={r.href}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-secondary/50"
          >
            <Badge variant="accent">
              <KindIcon kind={r.kind} />
              {KIND_LABEL[r.kind]}
            </Badge>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13.5px] font-medium">{r.title}</p>
              {r.excerpt && (
                <p className="truncate text-[12px] text-muted-foreground">
                  {r.excerpt}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3 text-[11.5px] text-muted-foreground">
              <span>{r.projectLabel}</span>
              <span>·</span>
              <span>{relativeTime(r.ts)}</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}

interface SkeletonProps { count?: number }
export function RecentActivitySkeleton({ count = 3 }: SkeletonProps) {
  return (
    <div className="space-y-2 rounded-xl border border-border bg-card p-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}
