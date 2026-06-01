import { api } from "@/lib/api";
import { LiveTile } from "@/components/live-tile";
import { StatusBadge } from "@/components/status-badge";
import { SeriesChart } from "@/components/series-chart";
import { DeviceMap } from "@/components/device-map";
import type { Summary, Device } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  let summary: Summary;
  try { summary = await api.summary(); }
  catch { summary = { devices_online: 0, kwh_today: 0, liters_today: 0, active_alerts: 0, as_of: new Date().toISOString() }; }

  let devices: Device[] = [];
  try { devices = await api.devices(); } catch {}

  return (
    <main className="p-8">
      <header className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Live campus sustainability</p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight">Water &amp; Energy Intelligence</h1>
          <p className="text-slate-400 mt-1">German Jordanian University · Madaba, Jordan</p>
        </div>
        <span className="text-xs text-slate-500">As of {new Date(summary.as_of).toLocaleTimeString()}</span>
      </header>

      <section className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <LiveTile label="Energy today"  value={summary.kwh_today}    unit="kWh"   accent="energy" digits={2} />
        <LiveTile label="Water today"   value={summary.liters_today} unit="liters" accent="water" digits={0} />
        <LiveTile label="Active alerts" value={summary.active_alerts} unit=""      digits={0} />
      </section>

      <section className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">Wheel power (last hour)</h2>
          <SeriesChart deviceId="wheel-01" metric="power" field="p" unit="W" color="#fbbf24" />
        </div>
        <div>
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">Library flow (last hour)</h2>
          <SeriesChart deviceId="flow-lib" metric="flow" field="lpm" unit="L/m" color="#38bdf8" />
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-3">Campus map</h2>
        <DeviceMap devices={devices} />
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-3">Devices</h2>
        <ul className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {devices.map(d => (
            <li key={d.id} className="rounded-xl bg-slate-900/60 border border-slate-800 p-4">
              <div className="text-sm text-slate-300">{d.label}</div>
              <div className="text-xs text-slate-500 font-mono">{d.id}</div>
              <div className="mt-2"><StatusBadge lastSeen={d.last_seen} /></div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
