import { api } from "@/lib/api";
import { LiveTile } from "@/components/live-tile";
import { SeriesChart } from "@/components/series-chart";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

type DeviceData = {
  id: string;
  label: string;
  last_seen: string | null;
  latest: Record<string, { ts: string; payload: Record<string, number | boolean | string> }>;
};

export default async function BuildingDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let d: DeviceData;
  try { d = await api.device(id) as unknown as DeviceData; }
  catch { d = { id, label: id, last_seen: null, latest: {} }; }
  const flow = (d.latest.flow?.payload ?? {}) as Record<string, number>;
  return (
    <main className="p-8">
      <div className="flex items-baseline justify-between">
        <h1 className="text-3xl font-bold">{d.label}</h1>
        <StatusBadge lastSeen={d.last_seen} />
      </div>
      <section className="mt-8 grid grid-cols-2 gap-4">
        <LiveTile label="Now"   value={flow.lpm ?? 0}     unit="L/min"  accent="water" />
        <LiveTile label="Total" value={flow.total_l ?? 0} unit="liters" accent="water" digits={0}/>
      </section>
      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">Flow (last 24h)</h2>
        <SeriesChart deviceId={id} metric="flow" field="lpm" bucket="5m" rangeMinutes={1440} unit="L/m" color="#38bdf8"/>
      </section>
    </main>
  );
}
