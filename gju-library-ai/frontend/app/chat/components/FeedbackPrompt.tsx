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
    setDone(rating === 1 ? T[lang].yes : rating === -1 ? T[lang].no : T[lang].skip);
  }
  if (done) return <p className="text-xs text-neutral-500">✓ {done}</p>;
  return (
    <div className="text-xs text-neutral-500 flex items-center gap-2">
      <span>{T[lang].helpful}</span>
      <button className="underline" onClick={() => send(1)}>{T[lang].yes}</button>
      <button className="underline" onClick={() => send(-1)}>{T[lang].no}</button>
      <button className="underline" onClick={() => send(null)}>{T[lang].skip}</button>
    </div>
  );
}
