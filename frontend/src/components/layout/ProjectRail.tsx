import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Plus, Folder, LogOut, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { TrustBadges } from "@/components/layout/TrustBadges";
import { useAuthStore } from "@/store/auth";
import { useSelectionStore } from "@/store/selection";
import { useProjects } from "@/hooks/use-projects";
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog";
import { authApi } from "@/api/auth";

const RECENT_LIMIT = 5;

export function ProjectRail() {
  const { data: projects = [], isLoading } = useProjects();
  const navigate = useNavigate();
  const params = useParams<{ projectId?: string }>();
  const activeProjectId =
    params.projectId ?? useSelectionStore.getState().activeProjectId;
  const setActiveProject = useSelectionStore((s) => s.setActiveProject);
  const username = useAuthStore((s) => s.username);
  const clearAuth = useAuthStore((s) => s.clear);

  const [showAll, setShowAll] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const visible = useMemo(
    () => (showAll ? projects : projects.slice(0, RECENT_LIMIT)),
    [projects, showAll],
  );

  const handleSignOut = async () => {
    const token = useAuthStore.getState().token;
    if (token) {
      try {
        await authApi.logout(token);
      } catch {
        // best effort
      }
    }
    clearAuth();
    navigate("/login");
  };

  return (
    <aside className="flex w-[264px] shrink-0 flex-col border-r border-border bg-secondary">
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <Link to="/" className="text-sm font-semibold tracking-tight">
          SecurePsych
        </Link>
      </div>

      <div className="px-3 pb-2">
        <Button
          variant="default"
          size="sm"
          className="w-full justify-start"
          onClick={() => setCreateOpen(true)}
        >
          <Plus className="h-4 w-4" />
          New project
        </Button>
      </div>

      <Separator />

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <p className="px-2 pb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Recent projects
        </p>

        {isLoading ? (
          <div className="space-y-1.5 px-2">
            <div className="h-7 animate-pulse rounded-md bg-background/60" />
            <div className="h-7 animate-pulse rounded-md bg-background/60" />
          </div>
        ) : visible.length === 0 ? (
          <p className="px-2 py-2 text-[12px] text-muted-foreground">
            No projects yet. Click <span className="font-medium">New project</span> to start.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {visible.map((p) => {
              const active = activeProjectId === p.id;
              return (
                <li key={p.id}>
                  <Link
                    to={`/p/${p.id}`}
                    onClick={() => setActiveProject(p.id)}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-2 py-1.5 text-[13px] transition-colors",
                      active
                        ? "bg-background font-medium text-foreground shadow-seg-active"
                        : "text-foreground/80 hover:bg-background/70",
                    )}
                  >
                    <Folder className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="truncate">{p.display_label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}

        {projects.length > RECENT_LIMIT && (
          <button
            type="button"
            onClick={() => setShowAll((v) => !v)}
            className="mt-1 px-2 py-1.5 text-[12px] text-muted-foreground hover:text-foreground"
          >
            {showAll ? "Show less" : `Load more (${projects.length - RECENT_LIMIT})`}
          </button>
        )}
      </nav>

      <Separator />

      <div className="space-y-3 px-3 py-3">
        <TrustBadges />
        <div className="flex items-center justify-between gap-2 rounded-md bg-background/60 px-2 py-1.5 text-[12px]">
          <span className="truncate">{username ?? "Signed in"}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleSignOut}
            title="Sign out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    </aside>
  );
}
