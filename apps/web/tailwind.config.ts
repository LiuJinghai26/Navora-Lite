import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#07111f",
        panel: "#0d1728",
        panelSoft: "#111f34",
        stroke: "#23344f",
        cyanEdge: "#22d3ee"
      },
      boxShadow: {
        glow: "0 0 32px rgba(34, 211, 238, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;

