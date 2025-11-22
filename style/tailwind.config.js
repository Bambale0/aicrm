/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        'van-gogh': {
          'ultramarine': '#003366',
          'cadmium-yellow': '#FFED4E',
          'chrome-green': '#4CAF50',
          'vermilion': '#E34234',
          'starry-night-blue': '#1B2631',
          'wheat-field': '#F4E4BC',
        },
      },
      animation: {
        'swirl': 'swirl 4s ease-in-out infinite',
        'brush-stroke': 'brush-stroke 3s ease-in-out infinite',
        'color-shift': 'color-shift 5s ease-in-out infinite',
      },
      keyframes: {
        swirl: {
          '0%': { transform: 'rotate(0deg) scale(1)' },
          '25%': { transform: 'rotate(90deg) scale(1.1)' },
          '50%': { transform: 'rotate(180deg) scale(0.9)' },
          '75%': { transform: 'rotate(270deg) scale(1.05)' },
          '100%': { transform: 'rotate(360deg) scale(1)' },
        },
        'brush-stroke': {
          '0%': { transform: 'translateX(-100%) skewX(-15deg)' },
          '50%': { transform: 'translateX(100%) skewX(15deg)' },
          '100%': { transform: 'translateX(-100%) skewX(-15deg)' },
        },
        'color-shift': {
          '0%': { backgroundColor: '#003366' },
          '25%': { backgroundColor: '#FFED4E' },
          '50%': { backgroundColor: '#4CAF50' },
          '75%': { backgroundColor: '#E34234' },
          '100%': { backgroundColor: '#003366' },
        },
      },
    },
  },
  plugins: [],
}
