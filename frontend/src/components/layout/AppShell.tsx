import { Outlet } from "react-router-dom";
import { ProjectRail } from "@/components/layout/ProjectRail";

export function AppShell() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <ProjectRail />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
