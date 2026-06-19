/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', '"Noto Sans SC"', 'system-ui', 'sans-serif'] },
      boxShadow: { soft: '0 18px 55px rgba(82, 65, 170, .10)' },
    },
  },
  plugins: [],
}
