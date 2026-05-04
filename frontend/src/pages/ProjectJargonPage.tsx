import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Copy, Sparkles, Languages } from "lucide-react";

import { TopBar } from "@/components/layout/TopBar";
import { ToolSwitcher } from "@/components/layout/ToolSwitcher";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { LevelSelector } from "@/components/jargon/LevelSelector";
import { useProject } from "@/hooks/use-projects";
import { useJargon } from "@/hooks/use-jargon";
import { useSelectionStore } from "@/store/selection";
import { useToast } from "@/hooks/use-toast";
import { apiErrorMessage } from "@/api/client";
import type { JargonLevel, JargonResponse } from "@/types/api";

const MAX_INPUT = 4000;

export default function ProjectJargonPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const { data: project } = useProject(projectId);
  const [level, setLevel] = useState<JargonLevel>(3);
  const [text, setText] = useState("");
  const [result, setResult] = useState<JargonResponse | null>(null);
  const mut = useJargon();
  const { toast } = useToast();

  useEffect(() => {
    if (projectId) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  const onSimplify = async (chosenLevel?: JargonLevel) => {
    if (!projectId || !text.trim()) return;
    const reqLevel = chosenLevel ?? level;
    try {
      const res = await mut.mutateAsync({
        text: text.trim(),
        level: reqLevel,
        project_id: projectId,
      });
      setResult(res);
    } catch (err) {
      toast({
        title: "Simplify failed",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  const onLevelChange = (l: JargonLevel) => {
    setLevel(l);
    if (result) onSimplify(l);
  };

  const onCopy = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.simplified_text).catch(() => {});
    toast({ title: "Copied", variant: "success" });
  };

  if (!projectId) return null;

  return (
    <>
      <TopBar
        breadcrumbs={[
          { label: "SecurePsych AI", to: "/" },
          { label: project?.display_label ?? "Project", to: `/p/${projectId}` },
          { label: "Simplify" },
        ]}
        rightSlot={<ToolSwitcher projectId={projectId} />}
      />
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <header className="space-y-1">
            <h1 className="text-[19px] font-semibold tracking-tight">Simplify</h1>
            <p className="text-[13px] text-muted-foreground">
              Rewrite clinical text at a chosen reading level. Input is never stored beyond a
              200-character preview.
            </p>
          </header>

          <Card>
            <CardContent className="space-y-3 p-5">
              <p className="text-[12.5px] font-medium uppercase tracking-wide text-muted-foreground">
                Reading level
              </p>
              <LevelSelector value={level} onChange={onLevelChange} disabled={mut.isPending} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-medium">Clinical input</p>
                  <span className="text-[11.5px] text-muted-foreground">
                    {text.length}/{MAX_INPUT}
                  </span>
                </div>
                <Textarea
                  value={text}
                  onChange={(e) => setText(e.target.value.slice(0, MAX_INPUT))}
                  rows={10}
                  placeholder="Paste clinical text — e.g., 'The examinee demonstrated significant deficits in phonological processing…'"
                  className="min-h-[200px] resize-y"
                />
                <Button
                  type="button"
                  size="lg"
                  className="w-full"
                  onClick={() => onSimplify()}
                  disabled={mut.isPending || text.trim().length === 0}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {mut.isPending ? "Simplifying…" : `Simplify at Level ${level}`}
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-secondary/40">
              <CardContent className="space-y-3 p-5">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Languages className="h-3.5 w-3.5 text-muted-foreground" />
                    <p className="text-[13px] font-medium">Plain-language rewrite</p>
                  </div>
                  {result && (
                    <div className="flex items-center gap-1.5">
                      <Badge variant="accent">Level {result.level}</Badge>
                      <Badge variant="default">FK {result.flesch_kincaid_grade.toFixed(1)}</Badge>
                    </div>
                  )}
                </div>

                {mut.isPending ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-4/6" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : result ? (
                  <p className="whitespace-pre-wrap text-[14px] leading-[1.7]">
                    {result.simplified_text}
                  </p>
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    Pick a reading level, paste clinical text on the left, and click Simplify.
                  </p>
                )}

                {result && !mut.isPending && (
                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <span className="text-[11.5px] text-muted-foreground">
                      Input preview stored for history (first 200 chars only).
                    </span>
                    <Button type="button" variant="ghost" size="sm" onClick={onCopy}>
                      <Copy className="h-3 w-3" />
                      Copy
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
