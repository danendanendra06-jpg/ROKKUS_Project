/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#386438',      // Sidebar dark green
          light: '#9AC351',     // Light green for primary buttons, active items, "Aman"
          accent: '#F1AE00',    // Mustard accent
          cream: '#F6F1E2',     // Cream background
          creamLight: '#FAF8F5',
          darkHover: '#2d522d',
          lightHover: '#88ae43',
        },
        status: {
          aman: {
            bg: '#EAF4DC',
            text: '#2D5518',
            border: '#9AC351',
            dot: '#609B26'
          },
          menipis: {
            bg: '#FEF3C7',
            text: '#B45309',
            border: '#FBBF24',
            dot: '#D97706'
          },
          habis: {
            bg: '#FEE2E2',
            text: '#B91C1C',
            border: '#FCA5A5',
            dot: '#DC2626'
          }
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
