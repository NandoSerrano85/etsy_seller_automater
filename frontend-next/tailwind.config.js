/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        accent: 'var(--accent)',
        surface: 'var(--surface)'
      },
      borderRadius: {
        DEFAULT: 'var(--radius)'
      }
    }
  },
  plugins: []
}