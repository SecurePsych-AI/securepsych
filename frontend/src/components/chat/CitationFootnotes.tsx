import { FileText, Copy } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { Citation } from "@/types/api";

interface Props {
  citations: Citation[];
  className?: string;
  onCopy?: (c: Citation) => void;
}

export function CitationFootnotes({ citations, className, onCopy }: Props) {
  if (citations.length === 0) return null;
  return (
    <ol className={cn("mt-3 space-y-1.5 border-t border-border pt-3", className)}>
      {citations.map((c, i) => (
        <li
          key={`${c.document_id}-${c.parent_id}-${i}`}
          className="flex items-start gap-2 text-[12.5px]"
        >
          <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-primary-soft bg-primary-soft font-mono text-[11px] text-primary">
            {i + 1}
          </span>
          <span className="flex flex-1 items-start gap-2">
            <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="min-w-0 flex-1">
              <span className="font-mono text-[12px]">{c.source}</span>
              <span className="text-muted-foreground"> · page {c.page}</span>
            </span>
            {onCopy && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-6 px-1.5 text-[11.5px]"
                onClick={() => onCopy(c)}
                title="Copy citation"
              >
                <Copy className="h-3 w-3" />
              </Button>
            )}
          </span>
        </li>
      ))}
    </ol>
  );
}
