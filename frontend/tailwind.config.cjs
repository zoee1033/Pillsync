module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F9CF9',
        'primary-green': '#4ADE80',
        background: '#F8FAFC',
        card: '#FFFFFF',
        'text-primary': '#1E293B',
        'text-secondary': '#64748B',
        border: '#E2E8F0',
      },
      borderRadius: {
        xl: '18px',
      },
    },
  },
  plugins: [],
};
