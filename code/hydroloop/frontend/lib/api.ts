import type { Device, Reading, Summary, Series } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  devices:     () => get<Device[]>("/api/devices"),
  device:      (id: string) => get<Device & { latest: Record<string, Reading> }>(`/api/devices/${id}`),
  series:      (id: string, metric: string, bucket = "1m", from?: string, to?: string) => {
    const q = new URLSearchParams({ metric, bucket, ...(from && {from}), ...(to && {to}) });
    return get<Series>(`/api/devices/${id}/series?${q}`);
  },
  summary:     () => get<Summary>("/api/summary"),
  events:      (since?: string) => get<unknown[]>(`/api/events${since ? `?since=${since}` : ""}`),
};

export const apiBase = BASE;
