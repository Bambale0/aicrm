/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        'van-gogh': {
          'ultramarine': '#2563eb',
          'cadmium-yellow': '#d97706',
          'chrome-green': '#64748b',
          'vermilion': '#dc2626',
          'starry-night-blue': '#0f172a',
          'wheat-field': '#475569',
        },
      },
    },
  },
  plugins: [],
}
