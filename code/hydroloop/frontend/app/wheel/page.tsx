import { api } from "@/lib/api";
import { LiveTile } from "@/components/live-tile";
import { SeriesChart } from "@/components/series-chart";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

type WheelData = {
  id: string;
  label: string;
  last_seen: string | null;
  latest: Record<string, { ts: string; payload: Record<string, number | boolean | string> }>;
};

export default async function WheelPage() {
  let d: WheelData;
  try { d = await api.device("wheel-01") as unknown as WheelData; }
  catch { d = { id: "wheel-01", label: "Central Water Wheel", last_seen: null, latest: {} }; }

  const power   = (d.latest.power?.payload   ?? {}) as Record<string, number>;
  const level   = (d.latest.level?.payload   ?? {}) as Record<string, number>;
  const weather = (d.latest.weather?.payload ?? {}) as Record<string, number>;

  return (
    <main className="p-8">
      <div className="flex items-baseline justify-between">
        <h1 className="text-3xl font-bold">{d.label}</h1>
        <StatusBadge lastSeen={d.last_seen} />
      </div>

      <section className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <LiveTile label="Power"        value={power.p ?? 0}   unit="W"   accent="energy" />
        <LiveTile label="Energy"       value={power.e ?? 0}   unit="kWh" accent="energy" digits={2}/>
        <LiveTile label="Water level"  value={level.cm ?? 0}  unit="cm"  accent="water"  />
        <LiveTile label="Air temp"     value={weather.t ?? 0} unit="°C" />
      </section>

      <section className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">Power (last 24h)</h2>
          <SeriesChart deviceId="wheel-01" metric="power" field="p" bucket="5m" rangeMinutes={1440} unit="W" color="#fbbf24"/>
        </div>
        <div>
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">Water level (last 24h)</h2>
          <SeriesChart deviceId="wheel-01" metric="level" field="cm" bucket="5m" rangeMinutes={1440} unit="cm" color="#38bdf8"/>
        </div>
      </section>
    </main>
  );
}
