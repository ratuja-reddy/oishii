/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}", "./**/templates/**/*.html"],
  theme: { 
    extend: {
      colors: {
        'cream': '#FAF2EF',
        'terracotta': '#CA6145',
        'dark-teal': '#2F4F4F',
        'dark-text': '#1E1E1E',
        'white': '#FFFFFF',
      }
    } 
  },
  plugins: [require("@tailwindcss/typography"), require("@tailwindcss/forms")],
};


