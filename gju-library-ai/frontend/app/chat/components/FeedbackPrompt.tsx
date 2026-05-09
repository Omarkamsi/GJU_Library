"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Lang } from "@/lib/types";
import { T } from "@/lib/i18n";

export function FeedbackPrompt({ queryId, lang }: { queryId: number; lang: Lang }) {
  const [done, setDone] = useState<string | null>(null);

  async function send(rating: number | null) {
    await api("/feedback", {
      method: "POST",
      body: JSON.stringify({ scope: "answer", query_id: queryId, rating }),
    });
    setDone(rating === 1 ? "✓" : rating === -1 ? "↺" : "·");
  }

  if (done) {
    return (
      <p className="text-[11px] text-gju-ink/45 ms-10">{done} {T[lang].helpful}</p>
    );
  }

  const btn = "inline-flex items-center justify-center w-7 h-7 rounded-full text-gju-ink/50 hover:text-gju-blue hover:bg-gju-blue-soft transition";

  return (
    <div className="ms-10 text-[11px] text-gju-ink/50 flex items-center gap-1">
      <span className="me-1">{T[lang].helpful}</span>
      <button className={btn} onClick={() => send(1)} title={T[lang].yes} aria-label={T[lang].yes}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 10v12" />
          <path d="M15 5.88L14 10h5.83a2 2 0 011.92 2.56l-2.4 8A2 2 0 0117.43 22H7V10l4-9c1.66 0 3 1.34 3 3v1.88z" />
        </svg>
      </button>
      <button className={btn} onClick={() => send(-1)} title={T[lang].no} aria-label={T[lang].no}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 14V2" />
          <path d="M9 18.12L10 14H4.17a2 2 0 01-1.92-2.56l2.4-8A2 2 0 016.57 2H17v12l-4 9c-1.66 0-3-1.34-3-3v-1.88z" />
        </svg>
      </button>
      <button className="text-[11px] text-gju-ink/40 hover:text-gju-ink/70 ms-1" onClick={() => send(null)}>
        {T[lang].skip}
      </button>
    </div>
  );
}
