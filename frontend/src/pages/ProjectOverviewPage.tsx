import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Folder, FileText, MessageSquare, Languages, Upload, Trash2, ShieldAlert } from "lucide-react";

import { TopBar } from "@/components/layout/TopBar";
import { ToolSwitcher } from "@/components/layout/ToolSwitcher";
import {
  useProject,
  useProjectFiles,
  useProjectThreads,
  useProjectSummaries,
  useProjectJargonRuns,
} from "@/hooks/use-projects";
import { useDeleteDocument } from "@/hooks/use-rag";
import { useSelectionStore } from "@/store/selection";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { apiErrorMessage } from "@/api/client";
import { relativeTime } from "@/lib/format";
import type { UploadedFile } from "@/types/api";

export default function ProjectOverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const { data: project, isLoading } = useProject(projectId);
  const { data: files = [] } = useProjectFiles(projectId);
  const { data: threads = [] } = useProjectThreads(projectId);
  const { data: summaries = [] } = useProjectSummaries(projectId);
  const { data: jargon = [] } = useProjectJargonRuns(projectId);
  const [deleteCandidate, setDeleteCandidate] = useState<UploadedFile | null>(null);
  const deleteMut = useDeleteDocument();
  const { toast } = useToast();

  useEffect(() => {
    if (projectId) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  const onConfirmDelete = async () => {
    if (!projectId || !deleteCandidate) return;
    const candidate = deleteCandidate;
    setDeleteCandidate(null);
    try {
      await deleteMut.mutateAsync({
        projectId,
        documentId: candidate.document_id,
      });
      toast({
        title: "Document deleted",
        description: `${candidate.filename_redacted} · ${candidate.chunks_added} chunks removed`,
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "Delete failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <TopBar
        breadcrumbs={[
          { label: "SecurePsych AI", to: "/" },
          { label: project?.display_label ?? "Loading…" },
        ]}
        rightSlot={projectId ? <ToolSwitcher projectId={projectId} /> : undefined}
      />
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-4xl space-y-8">
          <header className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Folder className="h-4 w-4 text-muted-foreground" />
                <h1 className="text-[19px] font-semibold tracking-tight">
                  {isLoading ? "Loading…" : project?.display_label}
                </h1>
              </div>
              <p className="text-[13px] text-muted-foreground">
                {project
                  ? `Created ${relativeTime(project.created_at)}`
                  : null}
              </p>
            </div>
            <Button asChild variant="default">
              <Link to={`/p/${projectId}/qa`}>
                <MessageSquare className="h-4 w-4" />
                Ask a question
              </Link>
            </Button>
          </header>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="flex items-center gap-2 text-[13.5px] font-semibold">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  Documents
                  <Badge variant="default">{files.length}</Badge>
                </CardTitle>
                <Button asChild variant="ghost" size="sm">
                  <Link to={`/p/${projectId}/qa`}>
                    <Upload className="h-3.5 w-3.5" /> Upload
                  </Link>
                </Button>
              </CardHeader>
              <CardContent>
                {files.length === 0 ? (
                  <p className="text-[13px] text-muted-foreground">
                    No documents yet. Upload a redacted PDF to start asking questions.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {files.map((f) => (
                      <li
                        key={f.id}
                        className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-[13px]"
                      >
                        <div className="min-w-0">
                          <p className="truncate font-medium">{f.filename_redacted}</p>
                          <p className="text-[11.5px] text-muted-foreground">
                            {f.chunks_added} chunks · {f.strategy} strategy ·{" "}
                            {relativeTime(f.uploaded_at)}
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteCandidate(f)}
                          className="text-muted-foreground hover:bg-destructive-soft hover:text-destructive"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[13.5px] font-semibold">
                  <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                  Threads
                  <Badge variant="default">{threads.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {threads.length === 0 ? (
                  <p className="text-[13px] text-muted-foreground">
                    Start a thread from the Q&A composer.
                  </p>
                ) : (
                  <ul className="space-y-1.5">
                    {threads.slice(0, 4).map((t) => (
                      <li key={t.id}>
                        <Link
                          to={`/p/${projectId}/qa/${t.id}`}
                          className="block rounded-md px-2 py-1.5 text-[13px] hover:bg-secondary"
                        >
                          <p className="truncate">{t.title ?? "Untitled thread"}</p>
                          <p className="text-[11.5px] text-muted-foreground">
                            {relativeTime(t.created_at)}
                          </p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[13.5px] font-semibold">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  Summaries
                  <Badge variant="default">{summaries.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {summaries.length === 0 ? (
                  <p className="text-[13px] text-muted-foreground">
                    No summaries yet.
                  </p>
                ) : (
                  <ul className="space-y-1.5">
                    {summaries.slice(0, 3).map((s) => (
                      <li key={s.id} className="rounded-md px-2 py-1.5 text-[13px]">
                        <p className="truncate font-medium">{s.filename_redacted}</p>
                        <p className="text-[11.5px] text-muted-foreground">
                          {s.page_count} pages · {relativeTime(s.created_at)}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[13.5px] font-semibold">
                  <Languages className="h-3.5 w-3.5 text-muted-foreground" />
                  Jargon runs
                  <Badge variant="default">{jargon.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {jargon.length === 0 ? (
                  <p className="text-[13px] text-muted-foreground">
                    No simplifications yet.
                  </p>
                ) : (
                  <ul className="space-y-1.5">
                    {jargon.slice(0, 3).map((j) => (
                      <li key={j.id} className="rounded-md px-2 py-1.5 text-[13px]">
                        <p className="truncate">
                          <Badge variant="accent">L{j.level}</Badge>{" "}
                          <span className="text-muted-foreground">
                            FK {j.fk_grade.toFixed(1)}
                          </span>
                        </p>
                        <p className="truncate text-[11.5px] text-muted-foreground">
                          {j.input_preview}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          {isLoading && (
            <div className="space-y-2">
              <Skeleton className="h-8 w-1/3" />
              <Skeleton className="h-32 w-full" />
            </div>
          )}
        </div>
      </div>

      <Dialog
        open={Boolean(deleteCandidate)}
        onOpenChange={(o) => !o && setDeleteCandidate(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Delete {deleteCandidate?.filename_redacted ?? "this document"}?
            </DialogTitle>
            <DialogDescription>
              All {deleteCandidate?.chunks_added ?? "indexed"} chunks and any
              citations referencing this document will be permanently removed.
              Past Q&amp;A threads will lose their source links.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-start gap-2 rounded-md border border-destructive-soft bg-destructive-soft px-3 py-2 text-[12.5px] text-destructive">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>Hard-delete · cannot be undone · required by FERPA.</span>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeleteCandidate(null)}
              disabled={deleteMut.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={onConfirmDelete}
              disabled={deleteMut.isPending}
            >
              {deleteMut.isPending ? "Deleting…" : "Delete permanently"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
