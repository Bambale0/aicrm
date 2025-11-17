import React, { useState, Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

// Core components - load immediately
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import BackgroundStars from './components/BackgroundVideo';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load pages for better performance
const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Customers = lazy(() => import('./pages/Customers'));
const Orders = lazy(() => import('./pages/Orders'));
const Tasks = lazy(() => import('./pages/Tasks'));
const Email = lazy(() => import('./pages/Email'));
const Telegram = lazy(() => import('./pages/Telegram'));
const Avito = lazy(() => import('./pages/Avito'));
const Users = lazy(() => import('./pages/Users'));
const Stages = lazy(() => import('./pages/Stages'));
const Triggers = lazy(() => import('./pages/Triggers'));
const AutomationLogs = lazy(() => import('./pages/AutomationLogs'));
const AIUsage = lazy(() => import('./pages/AIUsage'));
const Communications = lazy(() => import('./pages/Communications'));
const EmailManagement = lazy(() => import('./pages/EmailManagement'));
const ProductionSteps = lazy(() => import('./pages/ProductionSteps'));
const AISettings = lazy(() => import('./pages/AISettings'));
const AIManagerSettings = lazy(() => import('./pages/AIManagerSettings'));
const AvitoSettings = lazy(() => import('./pages/AvitoSettings'));
const TelegramSettings = lazy(() => import('./pages/TelegramSettings'));
const AutomationSettings = lazy(() => import('./pages/AutomationSettings'));
const AutomationBoard = lazy(() => import('./pages/AutomationBoard'));
const SystemSettings = lazy(() => import('./pages/SystemSettings'));
const EmailSettings = lazy(() => import('./pages/EmailSettings'));

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
  </div>
);

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <BackgroundStars />
                <div className="min-h-screen bg-transparent relative z-10">
                  {/* Мобильный overlay для sidebar */}
                  {sidebarOpen && (
                    <div
                      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-20 lg:hidden"
                      onClick={() => setSidebarOpen(false)}
                    />
                  )}

                  <div className="flex min-h-screen">
                    {/* Desktop sidebar */}
                    <div className="hidden lg:flex lg:w-64 lg:flex-col">
                      <Sidebar />
                    </div>

                  {/* Mobile sidebar */}
                  <div className={`fixed inset-y-0 left-0 z-30 w-64 transform transition-transform duration-300 ease-in-out lg:hidden ${
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                  }`}>
                    <div className="relative">
                      {/* Mobile sidebar header with close button */}
                      <div className="flex items-center justify-between p-4 border-b border-gray-700/30 lg:hidden">
                        <h2 className="text-lg font-semibold text-white">Меню</h2>
                        <button
                          onClick={() => setSidebarOpen(false)}
                          className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700/50 transition-colors"
                          aria-label="Закрыть меню"
                        >
                          <XMarkIcon className="w-6 h-6" />
                        </button>
                      </div>
                      <Sidebar onClose={() => setSidebarOpen(false)} />
                    </div>
                  </div>

                    {/* Main content */}
                    <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-br from-gray-900/80 via-gray-800/60 to-gray-900/80">
                      <Header onMenuClick={() => setSidebarOpen(true)} />
                      <main className="flex-1 p-4 sm:p-6 lg:p-8">
                        <div className="max-w-7xl mx-auto">
                          <ErrorBoundary>
                            <Suspense fallback={<PageLoader />}>
                              <Routes>
                                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                                <Route path="/dashboard" element={<Dashboard />} />
                                <Route path="/customers" element={<Customers />} />
                                <Route path="/orders" element={<Orders />} />
                                <Route path="/tasks" element={<Tasks />} />
                                <Route path="/users" element={<Users />} />
                                <Route path="/stages" element={<Stages />} />
                                <Route path="/triggers" element={<Triggers />} />
                                <Route path="/automation/logs" element={<AutomationLogs />} />
                                <Route path="/ai/usage" element={<AIUsage />} />
                                <Route path="/communications" element={<Communications />} />
                                <Route path="/email/management" element={<EmailManagement />} />
                                <Route path="/production/steps" element={<ProductionSteps />} />
                                <Route path="/email" element={<Email />} />
                                <Route path="/telegram" element={<Telegram />} />
                                <Route path="/avito" element={<Avito />} />
                                <Route path="/settings/ai" element={<AISettings />} />
                                <Route path="/settings/ai-manager" element={<AIManagerSettings />} />
                                <Route path="/settings/email" element={<EmailSettings />} />
                                <Route path="/settings/avito" element={<AvitoSettings />} />
                                <Route path="/settings/telegram" element={<TelegramSettings />} />
                                <Route path="/settings/automation" element={<AutomationSettings />} />
                                <Route path="/automation/board" element={<AutomationBoard />} />
                                <Route path="/settings/system" element={<SystemSettings />} />
                              </Routes>
                            </Suspense>
                          </ErrorBoundary>
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

export default App;
