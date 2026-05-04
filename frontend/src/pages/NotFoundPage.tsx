import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="space-y-3 text-center">
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
          404
        </p>
        <h1 className="text-xl font-semibold">Page not found</h1>
        <Button asChild variant="outline" size="sm">
          <Link to="/">Back to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
