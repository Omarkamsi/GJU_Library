"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

const ROTATION = ["/", "/wheel", "/buildings"];
const PERIOD_MS = 30_000;

export function KioskMode() {
  const sp = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const enabled = sp.get("kiosk") === "1";
  useEffect(() => {
    if (!enabled) return;
    const i = ROTATION.indexOf(path);
    const next = ROTATION[(Math.max(i, 0) + 1) % ROTATION.length];
    const t = setTimeout(() => router.push(`${next}?kiosk=1`), PERIOD_MS);
    return () => clearTimeout(t);
  }, [enabled, path, router]);
  if (!enabled) return null;
  return (
    <style>{`body { font-size: 1.15rem } header nav { display: none }`}</style>
  );
}
