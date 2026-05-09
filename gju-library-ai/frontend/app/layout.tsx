import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "GJU Library AI",
  description: "Trilingual library assistant for German Jordanian University.",
  icons: { icon: "/brand/gju-logo.png" },
  openGraph: {
    title: "GJU Library AI",
    description: "Ask the library — in English, العربية, or Deutsch.",
    images: ["/brand/gju-library-ai-og.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gju-paper text-gju-ink antialiased">
        {children}
      </body>
    </html>
  );
}
