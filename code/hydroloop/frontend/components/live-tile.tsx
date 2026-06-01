// frontend/components/live-tile.tsx
"use client";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { fmtNumber } from "@/lib/format";

interface Props {
  label: string;
  value: number;
  unit: string;
  digits?: number;
  accent?: "water" | "energy" | "neutral";
}

export function LiveTile({ label, value, unit, digits = 1, accent = "neutral" }: Props) {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    setPulse(true);
    const t = setTimeout(() => setPulse(false), 400);
    return () => clearTimeout(t);
  }, [value]);
  const color = accent === "water"  ? "text-water"
              : accent === "energy" ? "text-energy"
              : "text-slate-100";
  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-6 transition-colors duration-200 ease-out hover:border-slate-700">
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className={clsx(
        "mt-2 font-mono text-5xl font-semibold transition-opacity duration-300 ease-out tabular-nums",
        color,
        pulse && "opacity-70 motion-reduce:opacity-100",
      )}>
        {fmtNumber(value, digits)}
        <span className="ml-2 text-xl text-slate-500">{unit}</span>
      </div>
    </div>
  );
}
