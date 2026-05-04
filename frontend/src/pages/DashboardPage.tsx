import { TopBar } from "@/components/layout/TopBar";
import { FeatureCardGrid } from "@/components/dashboard/FeatureCardGrid";
import { RecentActivityList } from "@/components/dashboard/RecentActivityList";
import { useSelectionStore } from "@/store/selection";
import { useAuthStore } from "@/store/auth";

const HONORIFICS = new Set(["dr", "mr", "ms", "mrs", "prof"]);

function greetingName(username: string | null): string {
  if (!username) return "today";
  const parts = username.split(/[._]/).filter(Boolean);
  return parts
    .map((part, i) => {
      const lower = part.toLowerCase();
      const cap = lower[0]?.toUpperCase() + lower.slice(1);
      return i === 0 && HONORIFICS.has(lower) ? `${cap}.` : cap;
    })
    .join(" ");
}

export default function DashboardPage() {
  const projectId = useSelectionStore((s) => s.activeProjectId);
  const username = useAuthStore((s) => s.username);
  const name = greetingName(username);

  return (
    <>
      <TopBar />
      <div className="flex-1 overflow-y-auto px-8 py-10">
        <div className="mx-auto max-w-4xl space-y-10">
          <header className="space-y-2 text-center">
            <h1 className="text-[26px] font-semibold tracking-[-0.02em]">
              What should we do today, {name}?
            </h1>
            <p className="text-sm text-muted-foreground">
              {projectId
                ? "Pick a tool below to keep going."
                : "Pick a project from the rail, then pick a tool — or start a new case."}
            </p>
          </header>

          <FeatureCardGrid projectId={projectId} />

          <section className="space-y-3">
            <h2 className="text-[13px] font-semibold uppercase tracking-wide text-muted-foreground">
              Continue where you left off
            </h2>
            <RecentActivityList />
          </section>
        </div>
      </div>
    </>
  );
}
