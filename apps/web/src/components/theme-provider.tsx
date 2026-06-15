"use client";

import { useEffect } from "react";
import { applyTheme, getStoredTheme, isThemeName } from "@/lib/theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Sync the DOM theme on mount and when Settings broadcasts a theme change.
    applyTheme(getStoredTheme());
    const handleThemeChange = (event: Event) => {
      const theme = (event as CustomEvent).detail;
      if (isThemeName(theme)) applyTheme(theme);
    };
    window.addEventListener("navora-theme-change", handleThemeChange);
    return () => window.removeEventListener("navora-theme-change", handleThemeChange);
  }, []);

  return children;
}
