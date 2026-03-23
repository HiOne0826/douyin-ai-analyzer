import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      colors: {
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          900: '#111827',
        },
        blue: {
          600: '#2563eb',
        },
        dark: '#1a1a1a',
      },
      boxShadow: {
        'neo': '6px 6px 0px #1a1a1a',
        'neo-sm': '4px 4px 0px #1a1a1a',
        'neo-active': '2px 2px 0px #1a1a1a',
      },
      borderWidth: {
        '3': '3px',
      },
      transitionDuration: {
        '100': '100ms',
      }
    },
  },
  plugins: [],
}
export default config
