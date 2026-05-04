import { useMemo } from "react";
import { Copy, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

interface Section {
  anchor: string;
  title: string;
  body: string;
}

const HEADER_LINE = /^([A-Z][A-Za-z0-9 ()&,/-]{2,80}):\s*(.*)$/;

function parseSections(summary: string): Section[] {
  const blocks = summary
    .split(/\n\s*\n/)
    .map((b) => b.trim())
    .filter(Boolean);
  return blocks.map((block, i) => {
    const lines = block.split("\n");
    const first = lines[0].trim();
    let title: string;
    let body: string;
    const inline = first.match(HEADER_LINE);
    if (inline) {
      title = inline[1].trim();
      const rest = inline[2].trim();
      body = [rest, ...lines.slice(1)].filter(Boolean).join("\n").trim();
    } else if (/^[A-Z][A-Za-z0-9 ()&,/-]{2,80}:?\s*$/.test(first)) {
      title = first.replace(/:\s*$/, "");
      body = lines.slice(1).join("\n").trim();
    } else {
      title = `Section ${i + 1}`;
      body = block;
    }
    return {
      anchor: title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      title,
      body,
    };
  });
}

interface Props {
  summary: string;
  pageCount: number;
  filename?: string;
  streaming?: boolean;
}

export function SummaryDisplay({ summary, pageCount, filename, streaming }: Props) {
  const sections = useMemo(() => parseSections(summary), [summary]);
  const { toast } = useToast();

  const onCopy = () => {
    navigator.clipboard.writeText(summary).catch(() => {});
    toast({ title: "Summary copied", variant: "success" });
  };

  const onExport = () => {
    const blob = new Blob([summary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `summary_${(filename ?? "document").replace(/\.pdf$/i, "")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <h3 className="text-[14px] font-semibold tracking-tight">
            Psychoeducational summary
          </h3>
          {streaming ? (
            <Badge variant="warning">streaming…</Badge>
          ) : (
            <Badge variant="default">{pageCount} pages</Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={onCopy}>
            <Copy className="h-3.5 w-3.5" />
            Copy
          </Button>
          <Button variant="ghost" size="sm" onClick={onExport}>
            <Download className="h-3.5 w-3.5" />
            Export TXT
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[200px_minmax(0,1fr)]">
        <nav className="hidden border-r border-border p-3 lg:block">
          <ul className="space-y-0.5 text-[12.5px]">
            {sections.map((s) => (
              <li key={s.anchor}>
                <a
                  href={`#${s.anchor}`}
                  className="block truncate rounded-md px-2 py-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                >
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="space-y-5 p-5 text-[14px] leading-relaxed">
          {sections.map((s) => (
            <section key={s.anchor} id={s.anchor} className="space-y-1.5">
              <h4 className="text-[14.5px] font-semibold tracking-tight">{s.title}</h4>
              <div className="whitespace-pre-wrap text-foreground/90">{s.body}</div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
