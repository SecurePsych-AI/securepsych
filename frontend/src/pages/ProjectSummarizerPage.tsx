import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { FileText, Sparkles } from "lucide-react";

import { TopBar } from "@/components/layout/TopBar";
import { ToolSwitcher } from "@/components/layout/ToolSwitcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown } from "lucide-react";
import { UploadButton } from "@/components/upload/UploadButton";
import { SummaryDisplay } from "@/components/summarizer/SummaryDisplay";
import {
  useProject,
  useProjectFiles,
  useProjectSummaries,
} from "@/hooks/use-projects";
import {
  useSummarizeFromDocument,
  useSummarizeFromFile,
} from "@/hooks/use-summarizer";
import { useSelectionStore } from "@/store/selection";
import { useToast } from "@/hooks/use-toast";
import { apiErrorMessage } from "@/api/client";
import type { SummarizeResponse } from "@/types/api";

export default function ProjectSummarizerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const { data: project } = useProject(projectId);
  const { data: files = [] } = useProjectFiles(projectId);
  const { data: priorSummaries = [] } = useProjectSummaries(projectId);

  const [docId, setDocId] = useState<string | undefined>(files[0]?.document_id);
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [resultFilename, setResultFilename] = useState<string | undefined>(undefined);
  const fromDoc = useSummarizeFromDocument();
  const fromFile = useSummarizeFromFile();
  const { toast } = useToast();

  useEffect(() => {
    if (projectId) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  useEffect(() => {
    if (!docId && files[0]) setDocId(files[0].document_id);
  }, [docId, files]);

  const selectedFile = useMemo(
    () => files.find((f) => f.document_id === docId),
    [files, docId],
  );

  const busy = fromDoc.isPending || fromFile.isPending;

  const onGenerate = async () => {
    if (!projectId || !docId) return;
    try {
      const res = await fromDoc.mutateAsync({
        document_id: docId,
        project_id: projectId,
      });
      setResult(res);
      setResultFilename(selectedFile?.filename_redacted);
      toast({
        title: "Summary saved to project history",
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "Summarize failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  const onUploadAndSummarize = async (file: File) => {
    try {
      const res = await fromFile.mutateAsync({ file, projectId });
      setResult(res);
      setResultFilename(file.name);
      toast({
        title: "Summary ready",
        description: `${file.name} · ${res.page_count} pages`,
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "Summarize failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  if (!projectId) return null;

  return (
    <>
      <TopBar
        breadcrumbs={[
          { label: "SecurePsych AI", to: "/" },
          { label: project?.display_label ?? "Project", to: `/p/${projectId}` },
          { label: "Summarize" },
        ]}
        rightSlot={<ToolSwitcher projectId={projectId} />}
      />
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <header className="space-y-1">
            <h1 className="text-[19px] font-semibold tracking-tight">Summarize</h1>
            <p className="text-[13px] text-muted-foreground">
              Generate a structured psychoeducational summary from a project document.
              Saved to history automatically.
            </p>
          </header>

          <Card>
            <CardContent className="flex flex-wrap items-center gap-3 p-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary-soft text-primary">
                <FileText className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                {selectedFile ? (
                  <>
                    <p className="truncate text-[13.5px] font-medium">
                      {selectedFile.filename_redacted}
                    </p>
                    <p className="text-[11.5px] text-muted-foreground">
                      ~{selectedFile.chunks_added} chunks · {selectedFile.strategy} chunking
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-[13.5px] font-medium">No document selected</p>
                    <p className="text-[11.5px] text-muted-foreground">
                      Upload a PDF or pick one from this project.
                    </p>
                  </>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" disabled={files.length === 0}>
                      <FileText className="h-3.5 w-3.5" />
                      Switch document
                      <ChevronDown className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {files.map((f) => (
                      <DropdownMenuItem
                        key={f.document_id}
                        onSelect={() => setDocId(f.document_id)}
                      >
                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="truncate">{f.filename_redacted}</span>
                      </DropdownMenuItem>
                    ))}
                    {files.length === 0 && (
                      <DropdownMenuItem disabled>No documents</DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
                <UploadButton
                  onFile={onUploadAndSummarize}
                  disabled={busy}
                  variant="outline"
                  label="Or upload new"
                />
                <Button onClick={onGenerate} disabled={busy || !selectedFile}>
                  <Sparkles className="h-3.5 w-3.5" />
                  {busy ? "Generating…" : "Generate summary"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {busy && (
            <Card>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
                  <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary" />
                  Working on it… · summarizing {selectedFile?.filename_redacted ?? "document"}
                </div>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-4/6" />
              </CardContent>
            </Card>
          )}

          {result && !busy && (
            <SummaryDisplay
              summary={result.summary}
              pageCount={result.page_count}
              filename={resultFilename}
            />
          )}

          {!result && !busy && priorSummaries.length > 0 && (
            <SummaryDisplay
              summary={priorSummaries[0].summary}
              pageCount={priorSummaries[0].page_count}
              filename={priorSummaries[0].filename_redacted}
            />
          )}
        </div>
      </div>
    </>
  );
}
