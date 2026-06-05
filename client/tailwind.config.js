/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#060B18',
          secondary: '#0D1B2E',
          tertiary: '#0F2340',
        },
        surface: 'rgba(255,255,255,0.04)',
        glass: {
          DEFAULT: 'rgba(15,23,42,0.8)',
          light: 'rgba(255,255,255,0.05)',
          border: 'rgba(255,255,255,0.08)',
        },
        primary: {
          DEFAULT: '#6366F1',
          dim: 'rgba(99,102,241,0.15)',
          glow: 'rgba(99,102,241,0.4)',
          hover: '#4F46E5',
        },
        accent: {
          DEFAULT: '#8B5CF6',
          dim: 'rgba(139,92,246,0.15)',
        },
        success: '#10B981',
        danger: '#EF4444',
        brand: {
          text: '#E2E8F0',
          muted: '#94A3B8',
          dim: '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'gradient': 'gradient 6s ease infinite',
        'bounce-dot': 'bounceDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-gradient': 'radial-gradient(at 40% 20%, #1a0533 0px, transparent 50%), radial-gradient(at 80% 0%, #0d1b4a 0px, transparent 50%), radial-gradient(at 0% 50%, #0a0f2e 0px, transparent 50%), radial-gradient(at 80% 50%, #160d33 0px, transparent 50%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(99,102,241,0.3)',
        'glow-lg': '0 0 40px rgba(99,102,241,0.4)',
        'glass': '0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)',
        'card': '0 4px 24px rgba(0,0,0,0.3)',
      },
    },
  },
  plugins: [],
}
