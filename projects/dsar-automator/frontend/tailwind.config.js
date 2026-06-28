/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c5ca',
          300: '#9fa1a9',
          400: '#7b7d87',
          500: '#61636d',
          600: '#4d4e57',
          700: '#3f4047',
          800: '#2d2e33',
          900: '#1a1b1f',
          950: '#0f1012',
        },
        accent: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
        },
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
    },
  },
  plugins: [],
}
