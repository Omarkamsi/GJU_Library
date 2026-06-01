export type DeviceType = "wheel" | "flow" | "gateway";

export interface Device {
  id: string;
  type: DeviceType;
  label: string;
  location: { lat: number; lng: number; building?: string } | null;
  last_seen: string | null;
}

export interface Reading {
  device_id: string;
  metric: string;
  ts: string;
  payload: Record<string, number | boolean | string>;
}

export interface Summary {
  devices_online: number;
  kwh_today: number;
  liters_today: number;
  active_alerts: number;
  as_of: string;
}

export interface SeriesPoint { ts: string; [k: string]: number | string }
export interface Series {
  device_id: string;
  metric: string;
  bucket: string;
  points: SeriesPoint[];
}
