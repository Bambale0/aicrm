import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);

// Register service worker for PWA and performance optimization
serviceWorkerRegistration.register({
  onUpdate: (registration) => {
    // Notify user about available update
    if (window.confirm('New version available! Would you like to update?')) {
      // Tell the service worker to skip waiting
      registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  },
  onSuccess: (registration) => {
    console.log('Service Worker registered successfully with scope:', registration.scope);
  }
});
