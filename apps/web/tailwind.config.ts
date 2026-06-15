import type { Config } from "tailwindcss";

const config: Config = {
  // Scan only app source so generated files and dependencies do not affect CSS output.
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // CSS variables let runtime themes reuse the same Tailwind class names.
      colors: {
        surface: "var(--color-surface)",
        panel: "var(--color-panel)",
        panelSoft: "var(--color-panel-soft)",
        stroke: "var(--color-stroke)",
        cyanEdge: "var(--color-accent)"
      },
      boxShadow: {
        glow: "var(--shadow-glow)"
      }
    }
  },
  plugins: []
};

export default config;
