import { ArrowRight, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { RagPreviewResponse } from "@/types/api";

interface Props {
  preview: RagPreviewResponse;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}

function highlightWithEntities(
  text: string,
  entityMap: Record<string, string>,
  mode: "original" | "stored",
) {
  // Split sample_text on entity placeholders. Sample text uses placeholders like {STUDENT_NAME_1};
  // but sometimes raw values may appear. We render a tinted span around any token we can detect.
  const tokens = Object.keys(entityMap);
  const parts: Array<{ text: string; placeholder?: string }> = [];

  let remaining = text;
  while (remaining.length > 0) {
    let earliest = -1;
    let matchedToken: string | null = null;

    for (const t of tokens) {
      const idx = remaining.indexOf(t);
      if (idx !== -1 && (earliest === -1 || idx < earliest)) {
        earliest = idx;
        matchedToken = t;
      }
      const raw = entityMap[t];
      const idxRaw = remaining.indexOf(raw);
      if (idxRaw !== -1 && (earliest === -1 || idxRaw < earliest)) {
        earliest = idxRaw;
        matchedToken = t;
      }
    }

    if (earliest === -1 || matchedToken === null) {
      parts.push({ text: remaining });
      break;
    }
    if (earliest > 0) {
      parts.push({ text: remaining.slice(0, earliest) });
    }
    const tokLen =
      remaining.slice(earliest).startsWith(matchedToken)
        ? matchedToken.length
        : entityMap[matchedToken].length;
    parts.push({
      text: remaining.slice(earliest, earliest + tokLen),
      placeholder: matchedToken,
    });
    remaining = remaining.slice(earliest + tokLen);
  }

  return parts.map((p, i) => {
    if (!p.placeholder) return <span key={i}>{p.text}</span>;
    if (mode === "original") {
      return (
        <mark
          key={i}
          className="rounded-sm bg-warning-soft px-0.5 text-warning"
          title={p.placeholder}
        >
          {entityMap[p.placeholder]}
        </mark>
      );
    }
    return (
      <code
        key={i}
        className="rounded-sm bg-primary-soft px-1 py-px font-mono text-[12.5px] text-primary"
        title={`Replaces: ${entityMap[p.placeholder]}`}
      >
        {`{${p.placeholder}}`}
      </code>
    );
  });
}

export function PIIReviewPanel({ preview, onConfirm, onCancel, busy }: Props) {
  const entityCount = Object.keys(preview.entity_map).length;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-start justify-between gap-4 border-b border-border bg-secondary/40 px-8 py-5">
        <div className="space-y-1">
          <h1 className="text-[19px] font-semibold tracking-tight">
            Confirm what gets stored
          </h1>
          <p className="text-[13px] text-muted-foreground">
            <span className="font-medium text-foreground">{preview.filename}</span>{" "}
            · {preview.page_count} pages · {entityCount} entities detected
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={busy}>
            {busy ? "Ingesting…" : "Confirm and ingest"}
            {!busy && <ArrowRight className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="overflow-hidden">
              <CardHeader className="border-b border-border bg-warning-soft/40 py-3">
                <CardTitle className="text-[12.5px] font-semibold uppercase tracking-wide text-warning">
                  Original — discarded
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-60 overflow-y-auto p-4 text-[13.5px] leading-relaxed">
                {highlightWithEntities(preview.sample_text, preview.entity_map, "original")}
              </CardContent>
            </Card>

            <Card className="overflow-hidden">
              <CardHeader className="border-b border-border bg-primary-soft/40 py-3">
                <CardTitle className="text-[12.5px] font-semibold uppercase tracking-wide text-primary">
                  Stored — what we keep
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-60 overflow-y-auto p-4 text-[13.5px] leading-relaxed">
                {highlightWithEntities(preview.sample_text, preview.entity_map, "stored")}
              </CardContent>
            </Card>
          </div>

          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-success" />
                <p className="text-[13px] font-medium">Replacement map</p>
              </div>
              <Badge variant="default">standard chunking</Badge>
            </div>
            <ul className="divide-y divide-border">
              {Object.entries(preview.entity_map).map(([token, original]) => (
                <li key={token} className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-2 text-[13px]">
                  <span className="truncate font-mono text-warning">{original}</span>
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  <code className="truncate rounded-md border border-primary-soft bg-primary-soft px-1.5 py-0.5 font-mono text-[12px] text-primary">
                    {`{${token}}`}
                  </code>
                </li>
              ))}
            </ul>
          </div>

          <p className={cn("text-[12px] text-muted-foreground")}>
            Originals are never persisted regardless of choice. Cancel discards the upload session.
          </p>
        </div>
      </div>
    </div>
  );
}
