/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        night: "#0f172a",
        primary: {
          DEFAULT: "#6366f1",
          foreground: "#0f172a"
        }
      },
      boxShadow: {
        glass: "0 10px 40px rgba(99, 102, 241, 0.2)"
      },
      backdropBlur: {
        xs: "2px"
      }
    }
  },
  plugins: []
};
