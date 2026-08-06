module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0F8B6D',
        'primary-green': '#0F8B6D',
        secondary: '#C96E55',
        accent: '#C96E55',
        background: '#F8FAF8',
        card: '#FFFFFF',
        'text-primary': '#1F2937',
        'text-secondary': '#6B7280',
        border: '#E7ECE9',
        success: '#22C55E',
        warning: '#F59E0B',
        danger: '#EF4444',
      },
      borderRadius: {
        xl: '18px',
      },
    },
  },
  plugins: [],
};
