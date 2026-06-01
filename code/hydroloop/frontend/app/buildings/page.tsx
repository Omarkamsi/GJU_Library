import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";
import type { Device } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Buildings() {
  let all: Device[] = [];
  try { all = await api.devices(); } catch {}
  const flows = all.filter(d => d.type === "flow");
  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold">Buildings</h1>
      <ul className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {flows.map(d => (
          <li key={d.id}>
            <Link href={`/buildings/${d.id}`}
                  className="block rounded-2xl bg-slate-900/60 border border-slate-800 p-6 hover:border-water transition">
              <div className="text-lg font-semibold">{d.label}</div>
              <div className="text-xs text-slate-500 font-mono">{d.id}</div>
              <div className="mt-3"><StatusBadge lastSeen={d.last_seen} /></div>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
