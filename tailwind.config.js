/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}", "./**/templates/**/*.html"],
  theme: { extend: {} },
  plugins: [require("@tailwindcss/typography"), require("@tailwindcss/forms")],
};


