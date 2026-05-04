import { useEffect, useRef } from "react";
import { Copy, User, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { CitationFootnotes } from "@/components/chat/CitationFootnotes";
import type { ChatMessage } from "@/types/api";
import { useToast } from "@/hooks/use-toast";

interface Props {
  messages: ChatMessage[];
  pending?: boolean;
}

export function MessageList({ messages, pending }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, pending]);

  const onCopyMessage = (m: ChatMessage) => {
    navigator.clipboard.writeText(m.content).catch(() => {});
    toast({ title: "Copied", description: "Message copied to clipboard." });
  };

  return (
    <div ref={ref} className="flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-5">
        {messages.length === 0 && !pending && (
          <div className="rounded-xl border border-dashed border-border p-8 text-center text-[13px] text-muted-foreground">
            Ask a question about the documents in this project.
            <br />
            Every answer cites at least one source.
          </div>
        )}
        {messages.map((m) =>
          m.role === "user" ? (
            <div
              key={m.id}
              className="flex items-start justify-end gap-3"
            >
              <div className="max-w-[80%] rounded-2xl bg-primary px-4 py-2.5 text-[14.5px] leading-relaxed text-primary-foreground">
                {m.content}
              </div>
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
                <User className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
            </div>
          ) : (
            <div key={m.id} className="flex items-start gap-3">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Sparkles className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div
                  className={cn(
                    "rounded-2xl border border-border bg-card px-4 py-3 text-[15px] leading-relaxed",
                  )}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  <CitationFootnotes citations={m.sources} />
                  <div className="mt-3 flex items-center justify-between text-[12px] text-muted-foreground">
                    <span>
                      {m.sources.length > 0
                        ? `Cited ${m.sources.length} source${m.sources.length === 1 ? "" : "s"}`
                        : "No sources"}
                    </span>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => onCopyMessage(m)}
                      className="h-6 px-2 text-[11.5px]"
                    >
                      <Copy className="h-3 w-3" />
                      Copy
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ),
        )}
        {pending && (
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <div className="rounded-2xl border border-border bg-card px-4 py-4">
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary" />
                <span
                  className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary"
                  style={{ animationDelay: "0.2s" }}
                />
                <span
                  className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
