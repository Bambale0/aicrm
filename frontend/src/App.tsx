import React, { lazy, Suspense, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';

const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Requests = lazy(() => import('./pages/Requests'));
const Residents = lazy(() => import('./pages/Residents'));
const Buildings = lazy(() => import('./pages/Buildings'));
const Contractors = lazy(() => import('./pages/Contractors'));
const Messengers = lazy(() => import('./pages/Messengers'));
const Communications = lazy(() => import('./pages/Communications'));
const Users = lazy(() => import('./pages/Users'));
const AutomationBoard = lazy(() => import('./pages/AutomationBoard'));
const AIConnection = lazy(() => import('./pages/AIConnection'));

const AUTH_REQUIRED = process.env.REACT_APP_AUTH_REQUIRED !== 'false';

const PageLoader = () => (
  <div className="flex min-h-[320px] items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
  </div>
);

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={AUTH_REQUIRED ? <Login /> : <Navigate to="/dashboard" replace />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <div className="app-shell">
                  {sidebarOpen && (
                    <button
                      className="fixed inset-0 z-30 bg-slate-900/30 backdrop-blur-sm lg:hidden"
                      onClick={() => setSidebarOpen(false)}
                      aria-label="Закрыть меню"
                    />
                  )}

                  <div className="flex min-h-screen">
                    <div className={'hidden shrink-0 lg:block ' + (sidebarCollapsed ? 'w-20' : 'w-64')}>
                      <div className="fixed inset-y-0 left-0">
                        <Sidebar
                          collapsed={sidebarCollapsed}
                          onToggleCollapse={() => setSidebarCollapsed((value) => !value)}
                        />
                      </div>
                    </div>

                    <div className={'fixed inset-y-0 left-0 z-40 w-64 transform bg-white transition-transform duration-200 lg:hidden ' + (sidebarOpen ? 'translate-x-0' : '-translate-x-full')}>
                      <div className="absolute right-3 top-3 z-50">
                        <button
                          onClick={() => setSidebarOpen(false)}
                          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                          aria-label="Закрыть меню"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                      <Sidebar onClose={() => setSidebarOpen(false)} />
                    </div>

                    <div className="flex min-w-0 flex-1 flex-col">
                      <Header onMenuClick={() => setSidebarOpen(true)} />
                      <main className="flex-1 px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
                        <div className="mx-auto max-w-[1600px]">
                          <Routes>
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/requests" element={<Requests />} />
                            <Route path="/residents" element={<Residents />} />
                            <Route path="/buildings" element={<Buildings />} />
                            <Route path="/contractors" element={<Contractors />} />
                            <Route path="/messengers" element={<Messengers />} />
                            <Route path="/communications" element={<Communications />} />
                            <Route path="/users" element={<Users />} />
                            <Route path="/automation/board" element={<AutomationBoard />} />
                            <Route path="/ai" element={<AIConnection />} />
                            <Route path="*" element={<Navigate to="/dashboard" replace />} />
                          </Routes>
                        </div>
                      </main>
                    </div>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
