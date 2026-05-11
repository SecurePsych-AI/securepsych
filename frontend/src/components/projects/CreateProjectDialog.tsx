import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Lock } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { detectPiiInLabel } from "@/lib/ferpa";
import { useCreateProject } from "@/hooks/use-projects";
import { useSelectionStore } from "@/store/selection";
import { useToast } from "@/hooks/use-toast";
import { apiErrorMessage } from "@/api/client";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: Props) {
  const [label, setLabel] = useState("");
  const [studentId, setStudentId] = useState("");
  const [touched, setTouched] = useState(false);
  const navigate = useNavigate();
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const create = useCreateProject();
  const { toast } = useToast();

  const validation = useMemo(() => detectPiiInLabel(label), [label]);
  const showError = touched && !validation.ok;
  const showSuccess = touched && validation.ok && label.trim().length > 0;

  useEffect(() => {
    if (!open) {
      setLabel("");
      setStudentId("");
      setTouched(false);
    }
  }, [open]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!validation.ok) return;
    try {
      const project = await create.mutateAsync({
        display_label: label.trim(),
        student_id: studentId.trim() || undefined,
      });
      setActiveProject(project.id);
      toast({
        title: "Project created",
        description: project.display_label,
        variant: "success",
      });
      onOpenChange(false);
      navigate(`/p/${project.id}`);
    } catch (err) {
      toast({
        title: "Could not create project",
        description: apiErrorMessage(err),
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Start a new project</DialogTitle>
          <DialogDescription>
            One project per student case. Use a case code — never a name or birthdate.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="case-label">Case label</Label>
            <Input
              id="case-label"
              autoFocus
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={() => setTouched(true)}
              placeholder="Case 2026-014"
              maxLength={80}
              aria-invalid={showError ? true : undefined}
            />
            {showError && (
              <p className="flex items-start gap-1.5 text-[12px] text-destructive">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {!validation.ok ? validation.reason : null}
              </p>
            )}
            {showSuccess && (
              <p className="flex items-center gap-1.5 text-[12px] text-success">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Looks good. Format <span className="font-mono">Case 20XX-NNN</span> is recommended.
              </p>
            )}
            {!touched && (
              <p className="text-[12px] text-muted-foreground">
                Format <span className="font-mono">Case 20XX-NNN</span> is recommended.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="student-id">Internal student ID (optional)</Label>
            <Input
              id="student-id"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="district-id-98765"
            />
            <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
              <Lock className="h-3.5 w-3.5" />
              Sent once, never returned. Hashed with a keyed BLAKE2b function.
            </p>
          </div>

          <div className="rounded-lg bg-secondary p-3 text-[12px] leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground">Don't include</span> names, dates of birth, SSNs, or 6+ digit IDs in the label. The gateway will reject them.
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
