/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"DM Sans"',
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        ink: {
          50: "#f7f8fa",
          100: "#eceef2",
          200: "#d5dae3",
          300: "#aeb8c8",
          400: "#8290a8",
          500: "#637289",
          600: "#4e5c6f",
          700: "#404b5c",
          800: "#37404f",
          900: "#313845",
          950: "#0c0f14",
        },
        brand: {
          navy: "#1f2a44",
          green: "#43b047",
          amber: "#f4b000",
        },
        accent: {
          DEFAULT: "#43b047",
          dim: "rgba(67, 176, 71, 0.14)",
          muted: "#2f8f36",
        },
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to right, rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.07) 1px, transparent 1px)",
      },
      boxShadow: {
        card: "0 0 0 1px rgba(255,255,255,0.06) inset, 0 18px 50px rgba(0,0,0,0.45)",
        "card-light":
          "0 0 0 1px rgba(15,23,42,0.06) inset, 0 18px 50px rgba(15,23,42,0.08)",
        glow: "0 0 80px rgba(56, 189, 248, 0.12)",
      },
      animation: {
        shimmer: "shimmer 2.2s ease-in-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
