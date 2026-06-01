import "./globals.css";
import type { Metadata } from "next";
import { Suspense } from "react";
import { KioskMode } from "@/components/kiosk-mode";
import { SiteNav } from "@/components/site-nav";

export const metadata: Metadata = {
  title: "HydroLoop — GJU Water & Energy Intelligence",
  description: "Live campus sustainability dashboard from German Jordanian University.",
  icons: { icon: "/gju-logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen">
        <Suspense fallback={null}><KioskMode /></Suspense>
        <SiteNav />
        <div className="mx-auto max-w-7xl">{children}</div>
      </body>
    </html>
  );
}
