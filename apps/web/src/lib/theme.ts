export type ThemeName = "light" | "deep-blue" | "warm";

// Theme metadata powers the Settings page segmented choices.
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
  // Validate persisted or event-provided values before touching the DOM.
  return value === "light" || value === "deep-blue" || value === "warm";
}

export function getStoredTheme(): ThemeName {
  // Server rendering has no localStorage, so default to the base dark theme.
  if (typeof window === "undefined") return "deep-blue";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isThemeName(stored) ? stored : "deep-blue";
}

export function applyTheme(theme: ThemeName) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
}

export function storeTheme(theme: ThemeName) {
  // Broadcast changes so ThemeProvider and Settings stay in sync.
  window.localStorage.setItem(STORAGE_KEY, theme);
  applyTheme(theme);
  window.dispatchEvent(new CustomEvent("navora-theme-change", { detail: theme }));
}
