import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';

interface AdminRouteProps {
  children: React.ReactNode;
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { isAdmin, isLoading, sessionExpired } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <Navigate
        to="/login"
        state={{
          from: location,
          reason: sessionExpired ? 'expired' : 'required',
        }}
        replace
      />
    );
  }

  return <>{children}</>;
}
