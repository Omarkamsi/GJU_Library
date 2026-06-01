"use client";
import { useEffect, useRef } from "react";
import type { Device } from "@/lib/types";

// GJU Mushaqar campus centroid (OSM way 588418001).
// Address: Madaba St, Amman 17125, Jordan.
const CAMPUS_CENTER: [number, number] = [31.7770, 35.8014];
const DEFAULT_ZOOM = 18;

function statusTone(lastSeen: string | null): { bg: string; ring: string; label: string } {
  if (!lastSeen) return { bg: "#f43f5e", ring: "#9f1239", label: "offline" };
  const ageSec = (Date.now() - new Date(lastSeen).getTime()) / 1000;
  if (ageSec < 60)  return { bg: "#10b981", ring: "#064e3b", label: "live" };
  if (ageSec < 300) return { bg: "#f59e0b", ring: "#78350f", label: "stale" };
  return { bg: "#f43f5e", ring: "#9f1239", label: "offline" };
}

export function DeviceMap({ devices }: { devices: Device[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;
    let cleanupMarkers: Array<() => void> = [];

    (async () => {
      // Dynamic import — leaflet only runs client-side
      const L = (await import("leaflet")).default;

      // Inject Leaflet's CSS once (we don't ship its default icon set,
      // so we use divIcon — but the CSS still styles popups + zoom controls)
      if (!document.querySelector('link[data-leaflet-css]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        link.setAttribute("data-leaflet-css", "1");
        document.head.appendChild(link);
        // Wait one tick so CSS applies before we measure layout
        await new Promise(r => setTimeout(r, 0));
      }

      if (cancelled || !containerRef.current) return;

      // Init map
      const map = L.map(containerRef.current, {
        center: CAMPUS_CENTER,
        zoom: DEFAULT_ZOOM,
        zoomControl: true,
        scrollWheelZoom: false,
        attributionControl: true,
      });
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors',
      }).addTo(map);

      // Place a pin per device
      const positioned = devices.filter(d => d.location?.lat && d.location?.lng);
      positioned.forEach(d => {
        const t = statusTone(d.last_seen);
        const html = `
          <div style="
            width:18px;height:18px;border-radius:9999px;
            background:${t.bg};border:3px solid ${t.ring};
            box-shadow:0 0 0 3px rgba(0,0,0,0.25);
          "></div>`;
        const icon = L.divIcon({
          html,
          className: "",
          iconSize: [18, 18],
          iconAnchor: [9, 9],
        });
        const href = d.type === "wheel" ? "/wheel" : `/buildings/${d.id}`;
        const popup = `
          <strong>${d.label}</strong><br/>
          <span style="font-family:ui-monospace,monospace;font-size:11px;color:#64748b">${d.id}</span><br/>
          <span style="font-size:11px">status: ${t.label}</span><br/>
          <a href="${href}" style="color:#0369a1;text-decoration:underline">open →</a>`;
        const marker = L.marker([d.location!.lat, d.location!.lng], { icon })
          .addTo(map)
          .bindPopup(popup);
        cleanupMarkers.push(() => marker.remove());
      });

      // Fit bounds if devices are spread, otherwise stay at default zoom
      if (positioned.length > 1) {
        const bounds = L.latLngBounds(
          positioned.map(d => [d.location!.lat, d.location!.lng] as [number, number]),
        );
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 18 });
      }
    })();

    return () => {
      cancelled = true;
      cleanupMarkers.forEach(fn => fn());
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [devices]);

  return (
    <div
      ref={containerRef}
      className="h-80 w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-900"
      aria-label="Campus device map"
    />
  );
}
