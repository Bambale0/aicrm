/**
 * Lighthouse CI Configuration for AI CRM Frontend Performance Testing
 *
 * This configuration defines performance budgets, audit thresholds, and testing scenarios
 * for the AI CRM frontend application.
 */

module.exports = {
  ci: {
    collect: {
      // Test multiple scenarios
      numberOfRuns: 3,
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'Local:.*:3000',
      url: [
        'http://localhost:3000',
        'http://localhost:3000/login',
        'http://localhost:3000/dashboard',
        'http://localhost:3000/customers',
        'http://localhost:3000/orders'
      ]
    },

    // Performance budgets (resources)
    assert: {
      assertions: {
        // Bundle size budgets
        'resource-summary:script:size': ['error', { maxBytes: 2097152 }], // 2MB JS
        'resource-summary:stylesheet:size': ['error', { maxBytes: 512000 }], // 512KB CSS
        'resource-summary:font:size': ['error', { maxBytes: 102400 }], // 100KB fonts
        'resource-summary:image:size': ['warn', { maxBytes: 1048576 }], // 1MB images

        // Core Web Vitals
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['warn', { minScore: 0.8 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.8 }],

        // Performance metrics
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }], // < 1.5s FCP
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }], // < 2.5s LCP
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }], // < 0.1 CLS
        'first-input-delay': ['error', { maxNumericValue: 100 }], // < 100ms FID
        'total-blocking-time': ['error', { maxNumericValue: 300 }], // < 300ms TBT
        'speed-index': ['error', { maxNumericValue: 2500 }], // < 2.5s Speed Index
        'time-to-first-byte': ['error', { maxNumericValue: 800 }], // < 800ms TTFB

        // Network requests
        'network-requests': ['warn', { maxLength: 50 }], // Max 50 requests
        'uses-long-cache-ttl': ['warn', { maxLength: 10 }], // Check cache headers
        'uses-text-compression': ['error', { minScore: 0.9 }], // Gzip/brotli compression
        'uses-optimized-images': ['warn', { minScore: 0.8 }], // Image optimization

        // JavaScript/CSS issues
        'unused-javascript': ['warn', { maxLength: 5 }], // Max 5 unused JS files
        'unused-css-rules': ['warn', { maxLength: 10 }], // Max 10 unused CSS rules
        'render-blocking-resources': ['error', { maxLength: 0 }], // No render-blocking
        'unminified-javascript': ['error', { maxLength: 0 }], // All JS minified
        'unminified-css': ['error', { maxLength: 0 }], // All CSS minified

        // Security/PWA
        'has-hsts': ['warn', { minScore: 1 }], // HTTPS everywhere in prod
        'is-on-https': ['warn', { minScore: 1 }], // HTTPS required
        'service-worker': ['warn', { minScore: 1 }], // PWA service worker
        'installable-manifest': ['warn', { minScore: 1 }], // PWA manifest
        'works-offline': ['warn', { minScore: 0.7 }] // Offline capability
      }
    },

    // Upload results to temporary public storage
    upload: {
      target: 'temporary-public-storage'
    }
  }
};
