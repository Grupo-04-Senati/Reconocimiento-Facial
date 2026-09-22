import { Navigate, Outlet } from 'react-router-dom';
import { getSession } from '../store';
import type { Role } from '../types';

interface ProtectedRouteProps {
  allowedRoles?: Role[];
}

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const session = getSession();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(session.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
