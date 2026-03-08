import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#000000',
        accent: '#FF3B30',
        background: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Helvetica', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        'none': '0',
        'sm': '2px',
      },
      borderWidth: {
        '2': '2px',
        '4': '4px',
      }
    },
  },
  plugins: [],
}
export default config
