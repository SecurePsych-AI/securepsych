import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  const token = useAuthStore((s) => s.token);
  if (token) return <Navigate to="/" replace />;
  return <LoginForm />;
}
