import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gju: {
          ink: "#0F1929",
          blue: "#1B3A6E",
          "blue-soft": "#E8EEF8",
          gold: "#F5C518",
          "gold-soft": "#FFF6D1",
          teal: "#0E6E66",
          "teal-soft": "#DDF0EE",
          paper: "#FAF7F0",
        },
      },
      boxShadow: {
        bubble: "0 1px 2px rgba(15, 25, 41, 0.06), 0 4px 16px rgba(15, 25, 41, 0.04)",
        composer: "0 -1px 0 rgba(15,25,41,0.05), 0 -10px 24px rgba(15,25,41,0.04)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Inter",
          "Roboto", "Helvetica Neue", "Arial", "sans-serif",
        ],
        arabic: [
          "Noto Naskh Arabic", "Amiri", "Tajawal", "system-ui", "serif",
        ],
      },
    },
  },
  plugins: [],
};
export default config;
