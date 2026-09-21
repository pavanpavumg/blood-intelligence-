/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Tez.Health Brand Palette
        'tez-blue': {
          DEFAULT: '#0066FF',
          50: '#EBF3FF',
          100: '#D6E8FF',
          200: '#ADD1FF',
          300: '#85BAFF',
          400: '#5CA3FF',
          500: '#3385FF',
          600: '#0066FF',
          700: '#0052CC',
          800: '#003D99',
          900: '#002966',
        },
        'tez-yellow': {
          DEFAULT: '#FFD700',
          50: '#FFFBE6',
          100: '#FFF7CC',
          200: '#FFEF99',
          300: '#FFE766',
          400: '#FFDF33',
          500: '#FFD700',
          600: '#E6C200',
          700: '#B39800',
          800: '#806E00',
          900: '#4D4200',
        },
        // Legacy aliases for backward compatibility
        'primary-blue': '#0066FF',
        'bg-light-blue': '#EBF3FF',
        'bg-cream': '#FFFBE6',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}