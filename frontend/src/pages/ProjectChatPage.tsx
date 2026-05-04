import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Trash2 } from "lucide-react";

import { TopBar } from "@/components/layout/TopBar";
import { ToolSwitcher } from "@/components/layout/ToolSwitcher";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { MessageList } from "@/components/chat/MessageList";
import { Composer } from "@/components/chat/Composer";
import { PIIReviewPanel } from "@/components/upload/PIIReviewPanel";
import { useProject, useThread, useProjectFiles } from "@/hooks/use-projects";
import { useRagCommit, useRagPreview, useRagQuery, useDeleteDocument } from "@/hooks/use-rag";
import { useSelectionStore } from "@/store/selection";
import { useToast } from "@/hooks/use-toast";
import { apiErrorMessage } from "@/api/client";
import type { ChatMessage, RagPreviewResponse } from "@/types/api";

export default function ProjectChatPage() {
  const { projectId, threadId } = useParams<{
    projectId: string;
    threadId?: string;
  }>();
  const navigate = useNavigate();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const { data: project } = useProject(projectId);
  const { data: thread, isFetching: threadFetching } = useThread(projectId, threadId);
  const { data: files = [] } = useProjectFiles(projectId);

  const [draft, setDraft] = useState("");
  const [mode, setMode] = useState<"fast" | "deep">("fast");
  const [scopeId, setScopeId] = useState<string | undefined>(undefined);
  const [optimistic, setOptimistic] = useState<ChatMessage[]>([]);
  const [preview, setPreview] = useState<RagPreviewResponse | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<string | null>(null);

  const previewMut = useRagPreview();
  const commitMut = useRagCommit();
  const queryMut = useRagQuery();
  const deleteMut = useDeleteDocument();
  const { toast } = useToast();

  useEffect(() => {
    if (projectId) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  // Reset optimistic when navigating threads / fresh thread loads
  useEffect(() => {
    setOptimistic([]);
  }, [threadId]);

  const messages = useMemo<ChatMessage[]>(() => {
    const persisted = thread?.messages ?? [];
    return [...persisted, ...optimistic];
  }, [thread?.messages, optimistic]);

  const onSubmit = async () => {
    if (!projectId || !draft.trim()) return;
    const question = draft.trim();
    setDraft("");
    const tempUser: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: question,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setOptimistic((prev) => [...prev, tempUser]);
    try {
      const res = await queryMut.mutateAsync({
        question,
        project_id: projectId,
        thread_id: threadId,
        document_id: scopeId,
        mode,
      });
      // The mock handler persists user+assistant; the thread query has been
      // invalidated by the mutation. Clear optimistic so we don't double-render.
      setOptimistic([]);
      if (!threadId && res.thread_id) {
        navigate(`/p/${projectId}/qa/${res.thread_id}`, { replace: true });
      }
    } catch (err) {
      setOptimistic((prev) => prev.filter((m) => m.id !== tempUser.id));
      toast({
        title: "Question failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  const onUploadFile = async (file: File) => {
    try {
      const res = await previewMut.mutateAsync(file);
      setPreview(res);
    } catch (err) {
      toast({
        title: "Upload preview failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  const onConfirmIngest = async () => {
    if (!preview || !projectId) return;
    try {
      const res = await commitMut.mutateAsync({
        previewToken: preview.preview_token,
        projectId,
      });
      setPreview(null);
      toast({
        title: "Document ingested",
        description: `${res.source} · ${res.chunks_added} chunks`,
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "Ingest failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  const onConfirmDelete = async () => {
    if (!projectId || !deleteCandidate) return;
    const docId = deleteCandidate;
    setDeleteCandidate(null);
    try {
      await deleteMut.mutateAsync({ projectId, documentId: docId });
      toast({ title: "Document deleted", variant: "success" });
    } catch (err) {
      toast({
        title: "Delete failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  if (!projectId) return null;

  if (preview) {
    return (
      <PIIReviewPanel
        preview={preview}
        onConfirm={onConfirmIngest}
        onCancel={() => setPreview(null)}
        busy={commitMut.isPending}
      />
    );
  }

  return (
    <>
      <TopBar
        breadcrumbs={[
          { label: "SecurePsych AI", to: "/" },
          { label: project?.display_label ?? "Project", to: `/p/${projectId}` },
          { label: thread?.title ?? "Q&A" },
        ]}
        rightSlot={<ToolSwitcher projectId={projectId} />}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        {files.length === 0 ? (
          <div className="flex flex-1 items-center justify-center px-6">
            <div className="max-w-md rounded-xl border border-dashed border-border bg-card p-8 text-center">
              <h2 className="text-base font-semibold">Upload your first document</h2>
              <p className="mt-1.5 text-[13px] text-muted-foreground">
                The Q&A is grounded in this project's PDFs. Upload one to start asking questions.
              </p>
              <div className="mt-4">
                <Composer
                  projectId={projectId}
                  value=""
                  onChange={() => {}}
                  onSubmit={() => {}}
                  busy={previewMut.isPending}
                  mode={mode}
                  onModeChange={setMode}
                  scopedDocumentId={scopeId}
                  onScopeChange={setScopeId}
                  onUpload={onUploadFile}
                />
              </div>
            </div>
          </div>
        ) : (
          <>
            {files.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 border-b border-border bg-secondary/30 px-6 py-2 text-[12px] text-muted-foreground">
                <span className="font-medium text-foreground">In this project:</span>
                {files.map((f) => (
                  <span
                    key={f.id}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[11.5px]"
                  >
                    {f.filename_redacted}
                    <button
                      type="button"
                      title="Delete document"
                      onClick={() => setDeleteCandidate(f.document_id)}
                      className="ml-0.5 text-muted-foreground transition-colors hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            <MessageList
              messages={messages}
              pending={queryMut.isPending || threadFetching}
            />

            <div className="border-t border-border bg-secondary/30 px-6 py-3">
              <div className="mx-auto max-w-3xl">
                <Composer
                  projectId={projectId}
                  value={draft}
                  onChange={setDraft}
                  onSubmit={onSubmit}
                  busy={queryMut.isPending || previewMut.isPending}
                  mode={mode}
                  onModeChange={setMode}
                  scopedDocumentId={scopeId}
                  onScopeChange={setScopeId}
                  onUpload={onUploadFile}
                />
              </div>
            </div>
          </>
        )}
      </div>

      <Dialog
        open={Boolean(deleteCandidate)}
        onOpenChange={(o) => !o && setDeleteCandidate(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this document?</DialogTitle>
            <DialogDescription>
              All chunks and citations for this document will be permanently removed.
              Hard-delete · cannot be undone · required by FERPA.
            </DialogDescription>
          </DialogHeader>
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
