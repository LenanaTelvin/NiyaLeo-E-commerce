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
          DEFAULT: '#111827',   // near-black, your primary
          green: '#14532d',     // the one hover green, used everywhere
          greenSoft: '#f0fdf4', // faint green for hover backgrounds
          cream: '#FAF8F3',
        },
      },
    },
  },
  plugins: [],
}