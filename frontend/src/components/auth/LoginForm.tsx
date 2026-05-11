import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrustBadges } from "@/components/layout/TrustBadges";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/auth";
import { ApiError, apiErrorMessage } from "@/api/client";

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const expired =
    new URLSearchParams(location.search).get("expired") === "1";

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await authApi.login({ username, password });
      setSession(res.access_token, username);
      const from =
        (location.state as { from?: { pathname?: string } } | null)?.from
          ?.pathname ?? "/";
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) setError("Incorrect username or password.");
        else if (err.status === 429)
          setError("Too many attempts. Please wait a few minutes.");
        else setError(apiErrorMessage(err));
      } else {
        setError(apiErrorMessage(err));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-[360px] space-y-6">
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Sparkles className="h-5 w-5" />
          </div>
          <p className="text-sm font-semibold tracking-tight">SecurePsych</p>
        </div>

        <Card className="shadow-composer">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">Sign in</CardTitle>
            <p className="text-[13px] text-muted-foreground">
              Local server · session-only token
            </p>
          </CardHeader>
          <CardContent>
            {(error || expired) && (
              <div className="mb-3 flex items-start gap-2 rounded-md border border-destructive-soft bg-destructive-soft px-3 py-2 text-[12.5px] text-destructive">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>
                  {error ?? "Your session has expired. Sign in again."}
                </span>
              </div>
            )}
            <form onSubmit={onSubmit} className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  autoComplete="username"
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  autoComplete="current-password"
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button
                type="submit"
                size="xl"
                className="w-full"
                disabled={busy}
              >
                {busy ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <TrustBadges className="justify-center" />
      </div>
    </div>
  );
}
