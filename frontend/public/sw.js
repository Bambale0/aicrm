/**
 * AI CRM Service Worker - Offline Caching & Performance Optimization
 *
 * This service worker implements caching strategies for improved performance
 * and offline functionality using Workbox.
 */

// Import Workbox modules
importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');

if (workbox) {
  // Enable debug logging in development
  workbox.setConfig({ debug: false });

  // Precache critical resources
  workbox.precaching.precacheAndRoute([
    { url: '/', revision: '1' },
    { url: '/static/js/bundle.js', revision: '1' },
    { url: '/static/css/main.css', revision: '1' },
    { url: '/manifest.json', revision: '1' },
    { url: '/favicon.ico', revision: '1' },
  ]);

  // Runtime caching for API calls - use Network First strategy
  workbox.routing.registerRoute(
    ({ url }) => url.origin.includes('api') || url.pathname.startsWith('/api/'),
    new workbox.strategies.NetworkFirst({
      cacheName: 'api-cache',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 100,
          maxAgeSeconds: 60 * 60, // 1 hour
        }),
      ],
    })
  );

  // Cache images with StaleWhileRevalidate strategy
  workbox.routing.registerRoute(
    ({ request }) => request.destination === 'image',
    new workbox.strategies.StaleWhileRevalidate({
      cacheName: 'images',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 50,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        }),
      ],
    })
  );

  // Cache fonts with CacheFirst strategy (fonts rarely change)
  workbox.routing.registerRoute(
    ({ request }) => request.destination === 'font',
    new workbox.strategies.CacheFirst({
      cacheName: 'fonts',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
        }),
      ],
    })
  );

  // Cache static assets with CacheFirst strategy
  workbox.routing.registerRoute(
    ({ request }) =>
      request.destination === 'script' ||
      request.destination === 'style',
    new workbox.strategies.CacheFirst({
      cacheName: 'static-assets',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 100,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        }),
      ],
    })
  );

  // Background sync for failed API requests when back online
  workbox.routing.registerRoute(
    /\/api\/.*$/,
    new workbox.strategies.NetworkOnly({
      plugins: [
        new workbox.backgroundSync.BackgroundSyncPlugin('apiQueue', {
          maxRetentionTime: 24 * 60, // Retry for up to 24 hours
        }),
      ],
    }),
    'POST'
  );

  // Skip waiting and claim clients when service worker activates
  workbox.core.clientsClaim();
  workbox.core.skipWaiting();

  // Listen for messages from the main thread
  self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
      self.skipWaiting();
    }
  });

} else {
  console.log('Workbox could not be loaded. No offline caching available.');
}

// Handle install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installing.');
  self.skipWaiting();
});

// Handle activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating.');
  event.waitUntil(self.clients.claim());
});

// Handle fetch event (fallback for browsers without Workbox)
self.addEventListener('fetch', (event) => {
  // Only handle navigation requests for SPA
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        // Return cached offline page
        return caches.match('/');
      })
    );
  }
});
