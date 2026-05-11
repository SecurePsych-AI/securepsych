import { useEffect, useRef } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ModeToggle } from "@/components/chat/ModeToggle";
import { DocumentScopeFilter } from "@/components/chat/DocumentScopeFilter";
import { UploadButton } from "@/components/upload/UploadButton";

interface ComposerProps {
  projectId: string;
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy: boolean;
  mode: "fast" | "deep";
  onModeChange: (m: "fast" | "deep") => void;
  scopedDocumentId?: string;
  onScopeChange: (id?: string) => void;
  onUpload?: (file: File) => void;
}

export function Composer({
  projectId,
  value,
  onChange,
  onSubmit,
  busy,
  mode,
  onModeChange,
  scopedDocumentId,
  onScopeChange,
  onUpload,
}: ComposerProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = ref.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [value]);

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !busy) onSubmit();
    }
  };

  return (
    <form
      className="rounded-2xl border border-border bg-card shadow-composer"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim() && !busy) onSubmit();
      }}
    >
      <Textarea
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKey}
        rows={1}
        placeholder="Ask anything about this project's documents…"
        className="min-h-[44px] resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
      />
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <DocumentScopeFilter
            projectId={projectId}
            value={scopedDocumentId}
            onChange={onScopeChange}
          />
          <ModeToggle value={mode} onChange={onModeChange} />
        </div>
        <div className="flex items-center gap-1">
          {onUpload && <UploadButton onFile={onUpload} disabled={busy} />}
          <Button
            type="submit"
            size="sm"
            disabled={busy || value.trim().length === 0}
          >
            <Send className="h-3.5 w-3.5" />
            {busy ? "Sending…" : "Send"}
          </Button>
        </div>
      </div>
    </form>
  );
}
