/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        // Pastel color palette
        lavender: {
          25: '#fcfcff',
          50: '#f8f7ff',
          100: '#f0edff',
          200: '#e2dcff',
          300: '#c9bbff',
          400: '#b19aff',
          500: '#9679ff',
          600: '#7c5ce8',
          700: '#6442c4',
          800: '#523b99',
          900: '#43357a'
        },
        mint: {
          25: '#f8fffe',
          50: '#f0fdf9',
          100: '#ccfdf0',
          200: '#99fae1',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a'
        },
        peach: {
          25: '#fffcfa',
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12'
        },
        rose: {
          25: '#fffcfc',
          50: '#fff1f2',
          100: '#ffe4e6',
          200: '#fecdd3',
          300: '#fda4af',
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
          700: '#be123c',
          800: '#9f1239',
          900: '#881337'
        },
        sky: {
          25: '#fcfeff',
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e'
        },
        sage: {
          25: '#fbfcfb',
          50: '#f6f7f6',
          100: '#e8f0e8',
          200: '#d1e0d1',
          300: '#a8c5a8',
          400: '#7ba67b',
          500: '#5d8a5d',
          600: '#4a6f4a',
          700: '#3d583d',
          800: '#344834',
          900: '#2d3c2d'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} 