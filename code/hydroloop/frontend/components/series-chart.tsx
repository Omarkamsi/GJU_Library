// frontend/components/series-chart.tsx
"use client";
import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import type { SeriesPoint } from "@/lib/types";

interface Props {
  deviceId: string;
  metric: string;
  field: string;            // which key inside payload to plot, e.g. "lpm" | "p"
  bucket?: string;          // "1m" default
  rangeMinutes?: number;    // default 60
  unit?: string;
  color?: string;
}

export function SeriesChart({ deviceId, metric, field, bucket = "1m",
                              rangeMinutes = 60, unit = "", color = "#38bdf8" }: Props) {
  const [points, setPoints] = useState<SeriesPoint[]>([]);
  useEffect(() => {
    const to = new Date();
    const from = new Date(to.getTime() - rangeMinutes * 60_000);
    api.series(deviceId, metric, bucket, from.toISOString(), to.toISOString())
       .then(s => setPoints(s.points))
       .catch(() => setPoints([]));
  }, [deviceId, metric, bucket, rangeMinutes]);
  return (
    <div className="h-64 w-full rounded-2xl bg-slate-900/60 border border-slate-800/80 p-4">
      <ResponsiveContainer>
        <AreaChart data={points}>
          <defs>
            <linearGradient id={`g-${field}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"  stopColor={color} stopOpacity={0.5} />
              <stop offset="100%" stopColor={color} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="ts" hide />
          <YAxis stroke="#475569" fontSize={12} unit={unit} />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                   labelFormatter={(v) => new Date(v).toLocaleTimeString()} />
          <Area type="monotone" dataKey={field} stroke={color}
                fill={`url(#g-${field})`} strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
