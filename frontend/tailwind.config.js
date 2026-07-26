/** @type {import('tailwindcss').Config} */
export default {

  // Tell Tailwind: scan these files for class names
  // Any class you use in these files will be included in the final CSS
  // Any class NOT used gets stripped out — keeps the CSS file tiny
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      // Custom colors for FORGE dark theme
      // How to use them: bg-forge-bg, text-forge-text, border-forge-border
      colors: {
        forge: {
          bg:      '#0D0D14',  // main background — near black
          surface: '#13131F',  // sections and panels
          card:    '#1A1A2E',  // cards
          border:  '#2A2A3D',  // all borders
          purple:  '#7C3AED',  // main purple accent
          purpleh: '#8B5CF6',  // purple on hover
          cyan:    '#06B6D4',  // secondary cyan accent
          text:    '#F0F0FF',  // primary text — near white
          muted:   '#8B8BB3',  // secondary text
          dim:     '#5A5A7A',  // very faint text
          success: '#10B981',
          error:   '#EF4444',
          warning: '#F59E0B',
        }
      },
    },
  },
  plugins: [],
}