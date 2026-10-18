/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        tapbhoj: {
          bg: '#F1F4F0',
          'bg-dark': '#0E1714',
          surface: '#FFFFFF',
          'surface-dark': '#16231F',
          ink: '#14231E',
          'ink-dark': '#EAF1ED',
          muted: '#5D6B65',
          'muted-dark': '#9FB0A8',
          brand: '#123D33',
          'brand-dark': '#E8A317',
          accent: '#E8A317',
          veg: '#1F8A3B',
          'veg-dark': '#4CC16A',
          nonveg: '#C0392B',
          'nonveg-dark': '#EE6B5C',
          whatsapp: '#1F8A3B',
        },
      },
      fontFamily: {
        heading: ['"Bricolage Grotesque"', 'sans-serif'],
        body: ['Figtree', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
