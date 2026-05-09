"use client";
import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Stats = {
  totals: {
    queries: number;
    users: number;
    avg_latency_ms: number | null;
    p50_latency_ms: number | null;
    p95_latency_ms: number | null;
  };
  by_lang: { lang: string; n: number }[];
  database_ctr: {
    slug: string;
    name: string;
    shown: number;
    clicked: number;
    ctr_pct: string | number | null;
  }[];
  external_clicks: { shown: number; clicked: number };
  feedback: {
    scope: string;
    n: number;
    up: number;
    down: number;
    skip: number;
    avg_rating: string | number | null;
  }[];
  recent_queries: {
    id: number;
    lang: string;
    latency_ms: number;
    raw_query: string;
    answer_excerpt: string | null;
    created_at: string;
  }[];
};

const langLabel: Record<string, string> = { en: "English", ar: "العربية", de: "Deutsch" };

function ms(n: number | null | undefined) {
  if (n == null) return "—";
  return n >= 1000 ? `${(n / 1000).toFixed(1)} s` : `${n} ms`;
}

function Card({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl bg-white border border-gju-ink/5 shadow-bubble p-5 ${className}`}>
      <h2 className="text-xs uppercase tracking-wider text-gju-ink/55 mb-3">
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const [data, setData] = useState<Stats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const d = await api<Stats>("/admin/stats");
      setData(d);
      setErr(null);
    } catch (e: any) {
      const msg = String(e.message || e);
      if (msg.startsWith("401")) router.push("/login");
      else setErr(msg);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  if (err) {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="max-w-sm text-center">
          <h1 className="text-xl font-semibold mb-2">Admin only</h1>
          <p className="text-sm text-gju-ink/60">{err}</p>
          <Link href="/chat" className="text-gju-blue underline text-sm mt-4 inline-block">
            ← Back to chat
          </Link>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen flex items-center justify-center text-gju-ink/45 text-sm">
        Loading…
      </main>
    );
  }

  const t = data.totals;
  const totalQueries = t.queries || 0;
  const langTotal = data.by_lang.reduce((s, r) => s + r.n, 0) || 1;

  return (
    <main className="min-h-screen bg-gju-paper">
      <header className="sticky top-0 z-10 bg-gju-paper/85 backdrop-blur border-b border-gju-ink/5">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center gap-3">
          <Image
            src="/brand/gju-logo.png"
            alt="GJU"
            width={36}
            height={36}
            priority
            className="rounded-md"
          />
          <div className="flex-1 leading-tight">
            <div className="font-semibold">Library AI · Admin</div>
            <div className="text-[11px] text-gju-ink/55">
              Live usage · auto-refresh every 30s
            </div>
          </div>
          <Link
            href="/chat"
            className="text-xs text-gju-blue hover:text-gju-ink"
          >
            ← Back to chat
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-6 space-y-6">
        <section className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            ["Queries", totalQueries.toLocaleString()],
            ["Users", t.users.toLocaleString()],
            ["Avg latency", ms(t.avg_latency_ms)],
            ["p50 latency", ms(t.p50_latency_ms)],
            ["p95 latency", ms(t.p95_latency_ms)],
          ].map(([label, value]) => (
            <div
              key={label as string}
              className="rounded-xl bg-white border border-gju-ink/5 shadow-bubble px-4 py-3"
            >
              <div className="text-[10px] uppercase tracking-wider text-gju-ink/45">
                {label}
              </div>
              <div className="text-xl font-semibold mt-0.5">{value}</div>
            </div>
          ))}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card title="Queries by language">
            <ul className="space-y-2">
              {data.by_lang.map((r) => (
                <li key={r.lang} className="flex items-center gap-3">
                  <span className="w-16 text-xs uppercase font-medium text-gju-ink/70">
                    {langLabel[r.lang] || r.lang}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-gju-blue-soft overflow-hidden">
                    <div
                      className="h-full bg-gju-blue"
                      style={{ width: `${(100 * r.n) / langTotal}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-gju-ink/55 w-12 text-right">
                    {r.n}
                  </span>
                </li>
              ))}
              {data.by_lang.length === 0 && (
                <li className="text-xs text-gju-ink/45">no data</li>
              )}
            </ul>
          </Card>

          <Card title="Feedback" className="lg:col-span-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {data.feedback.length === 0 && (
                <p className="text-xs text-gju-ink/45">no feedback yet</p>
              )}
              {data.feedback.map((f) => (
                <div
                  key={f.scope}
                  className="rounded-xl bg-gju-paper/60 border border-gju-ink/5 p-4"
                >
                  <div className="text-xs uppercase tracking-wider text-gju-ink/55">
                    {f.scope}
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {f.avg_rating == null ? "—" : Number(f.avg_rating).toFixed(2)}
                    <span className="text-xs text-gju-ink/45 ms-2">avg</span>
                  </div>
                  <div className="mt-2 text-[12px] text-gju-ink/65 flex gap-3 font-mono">
                    <span title="thumbs up">👍 {f.up}</span>
                    <span title="thumbs down">👎 {f.down}</span>
                    <span title="skipped">· {f.skip}</span>
                    <span className="ms-auto text-gju-ink/40">n={f.n}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Database link counts">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] uppercase tracking-wider text-gju-ink/55">
                  <th className="text-start py-2">Database</th>
                  <th className="text-end py-2 w-24">Shown</th>
                  <th className="text-end py-2 w-24">Clicked</th>
                  <th className="text-end py-2 w-24">CTR</th>
                  <th className="py-2 ps-4">Bar</th>
                </tr>
              </thead>
              <tbody>
                {data.database_ctr.map((r) => {
                  const pct = Number(r.ctr_pct ?? 0);
                  return (
                    <tr key={r.slug} className="border-t border-gju-ink/5">
                      <td className="py-2">
                        <div>{r.name}</div>
                        <div className="text-[11px] text-gju-ink/40 font-mono">
                          {r.slug}
                        </div>
                      </td>
                      <td className="text-end font-mono text-gju-ink/70">
                        {r.shown}
                      </td>
                      <td className="text-end font-mono text-gju-ink/70">
                        {r.clicked}
                      </td>
                      <td className="text-end font-mono">
                        {r.ctr_pct == null ? "—" : `${pct.toFixed(1)}%`}
                      </td>
                      <td className="py-2 ps-4">
                        <div className="h-1.5 rounded-full bg-gju-gold-soft overflow-hidden">
                          <div
                            className="h-full bg-gju-gold"
                            style={{ width: `${Math.min(100, pct)}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {data.database_ctr.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-3 text-xs text-gju-ink/45">
                      no clicks yet
                    </td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="text-[11px] text-gju-ink/55 border-t border-gju-ink/5">
                  <td className="py-2">External (raw URLs)</td>
                  <td className="text-end font-mono">
                    {data.external_clicks.shown}
                  </td>
                  <td className="text-end font-mono">
                    {data.external_clicks.clicked}
                  </td>
                  <td className="text-end font-mono">
                    {data.external_clicks.shown
                      ? `${(
                          (100 * data.external_clicks.clicked) /
                          data.external_clicks.shown
                        ).toFixed(1)}%`
                      : "—"}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        </Card>

        <Card title="Recent queries">
          <ul className="divide-y divide-gju-ink/5">
            {data.recent_queries.map((q) => (
              <li key={q.id} className="py-2.5 flex items-start gap-3">
                <span
                  className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gju-blue-soft text-gju-blue mt-1"
                  title={q.created_at}
                >
                  {q.lang}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm truncate">{q.raw_query}</div>
                  {q.answer_excerpt && (
                    <div className="text-[11px] text-gju-ink/50 truncate">
                      {q.answer_excerpt}
                    </div>
                  )}
                </div>
                <span className="text-[11px] text-gju-ink/40 font-mono mt-1 shrink-0">
                  {ms(q.latency_ms)}
                </span>
              </li>
            ))}
            {data.recent_queries.length === 0 && (
              <li className="py-3 text-xs text-gju-ink/45">no queries yet</li>
            )}
          </ul>
        </Card>
      </div>
    </main>
  );
}
