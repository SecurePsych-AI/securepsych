import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";

interface Props {
  children: React.ReactNode;
}

export function RequireAuth({ children }: Props) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
