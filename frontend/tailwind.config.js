/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gem: {
          dark: '#0b2545',
          primary: '#134074',
          secondary: '#1d4ed8',
          accent: '#0284c7',
          amber: '#d97706',
          emerald: '#059669',
          ruby: '#dc2626',
          bg: '#f8fafc',
          surface: '#ffffff',
          border: '#e2e8f0'
        }
      }
    },
  },
  plugins: [],
}
