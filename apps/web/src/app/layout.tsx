import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

// Shared metadata for the Next.js App Router shell.
export const metadata: Metadata = {
  title: "Navora Lite",
  description: "Chat-first browser agent dashboard"
};

const themeInitScript = `
(function() {
  try {
    var theme = window.localStorage.getItem("navora-display-theme");
    if (theme === "light" || theme === "deep-blue" || theme === "warm") {
      document.documentElement.dataset.theme = theme;
    }
  } catch (error) {}
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Inline theme initialization prevents a dark-to-light flash before React mounts.
  return (
    <html lang="en" data-theme="deep-blue" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
