import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

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
