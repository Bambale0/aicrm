import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar.tsx';
import Header from './components/Header.tsx';
import ProtectedRoute from './components/ProtectedRoute.tsx';
import Login from './pages/Login.tsx';
import Dashboard from './pages/Dashboard.tsx';
import Customers from './pages/Customers.tsx';
import Orders from './pages/Orders.tsx';
import Tasks from './pages/Tasks.tsx';
import Email from './pages/Email.tsx';
import Telegram from './pages/Telegram.tsx';
import AISettings from './pages/AISettings.tsx';
import AIManagerSettings from './pages/AIManagerSettings.tsx';
import AvitoSettings from './pages/AvitoSettings.tsx';
import AutomationSettings from './pages/AutomationSettings.tsx';
import SystemSettings from './pages/SystemSettings.tsx';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-50">
              <div className="flex">
                <Sidebar />
                <div className="flex-1 flex flex-col">
                  <Header />
                  <main className="flex-1 p-6">
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/customers" element={<Customers />} />
                      <Route path="/orders" element={<Orders />} />
                      <Route path="/tasks" element={<Tasks />} />
                      <Route path="/email" element={<Email />} />
                      <Route path="/telegram" element={<Telegram />} />
                      <Route path="/settings/ai" element={<AISettings />} />
                      <Route path="/settings/ai-manager" element={<AIManagerSettings />} />
                      <Route path="/settings/avito" element={<AvitoSettings />} />
                      <Route path="/settings/automation" element={<AutomationSettings />} />
                      <Route path="/settings/system" element={<SystemSettings />} />
                    </Routes>
                  </main>
                </div>
              </div>
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
