/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Cormorant Garamond", "Georgia", "serif"],
        alt: ["Fraunces", "Georgia", "serif"]
      },
      colors: {
        esther: {
          cream: "#F7F4EF",
          sand: "#EBE6DD",
          olive: "#5C6648",
          "olive-soft": "#7A8568",
          herbal: "#6B7560",
          terracotta: "#CC733E",
          caramel: "#C28340",
          copper: "#DD8E4F",
          ink: "#2C2825",
          mist: "#F1EEE8",
          linen: "#F4F0EA"
        }
      }
    }
  },
  plugins: []
};

