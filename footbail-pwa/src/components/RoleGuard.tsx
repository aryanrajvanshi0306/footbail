import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

interface Props {
  children: ReactNode;
  allowed: string[];
}

export default function RoleGuard({ children, allowed }: Props) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (user && !allowed.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
