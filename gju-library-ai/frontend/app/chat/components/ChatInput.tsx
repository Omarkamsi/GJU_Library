"use client";
import { useState } from "react";
import type { Lang } from "@/lib/types";
import { T } from "@/lib/i18n";
import { dirOf } from "@/lib/i18n";

export function ChatInput({
  onSend,
  lang,
  busy,
}: {
  onSend: (q: string) => void;
  lang: Lang;
  busy?: boolean;
}) {
  const [v, setV] = useState("");
  const dir = dirOf(lang);
  return (
    <form
      dir={dir}
      className="flex items-center gap-2 bg-white border border-gju-ink/10 rounded-2xl shadow-bubble px-3 py-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!busy && v.trim()) {
          onSend(v.trim());
          setV("");
        }
      }}
    >
      <input
        value={v}
        onChange={(e) => setV(e.target.value)}
        placeholder={T[lang].askPlaceholder}
        className="flex-1 bg-transparent outline-none text-[15px] placeholder:text-gju-ink/35 px-1 py-1.5"
        autoFocus
      />
      <button
        type="submit"
        disabled={busy || !v.trim()}
        className="shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-xl bg-gju-blue text-white disabled:opacity-40 hover:bg-gju-ink transition"
        aria-label={T[lang].send}
        title={T[lang].send}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 2L11 13" />
          <path d="M22 2L15 22 11 13 2 9 22 2z" />
        </svg>
      </button>
    </form>
  );
}
