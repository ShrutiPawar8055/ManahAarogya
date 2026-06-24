import "./globals.css";
import { LanguageProvider } from "@/context/LanguageContext";

export const metadata = {
  title: "Manah Arogya",
  description: "Your wellness companion",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.cdnfonts.com/css/product-sans"
          rel="stylesheet"
        />
      </head>
      <body
        className="antialiased font-sans"
        style={{
          "--font-jakarta": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          "--font-geist-mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace",
          "--font-fjalla": "system-ui, sans-serif",
          "--font-jost": "system-ui, sans-serif",
        }}
      >
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
