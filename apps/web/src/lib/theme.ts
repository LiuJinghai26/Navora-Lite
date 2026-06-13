export type ThemeName = "light" | "deep-blue" | "warm";

export const THEME_OPTIONS: Array<{ value: ThemeName; label: string; description: string }> = [
  {
    value: "light",
    label: "Light",
    description: "Bright neutral workspace with green accents."
  },
  {
    value: "deep-blue",
    label: "Deep Blue",
    description: "Dark blue command-center style."
  },
  {
    value: "warm",
    label: "Warm",
    description: "Warm skin-tone palette with soft orange accents."
  }
];

const STORAGE_KEY = "navora-display-theme";

export function isThemeName(value: string | null): value is ThemeName {
  return value === "light" || value === "deep-blue" || value === "warm";
}

export function getStoredTheme(): ThemeName {
  if (typeof window === "undefined") return "deep-blue";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isThemeName(stored) ? stored : "deep-blue";
}

export function applyTheme(theme: ThemeName) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
}

export function storeTheme(theme: ThemeName) {
  window.localStorage.setItem(STORAGE_KEY, theme);
  applyTheme(theme);
  window.dispatchEvent(new CustomEvent("navora-theme-change", { detail: theme }));
}
