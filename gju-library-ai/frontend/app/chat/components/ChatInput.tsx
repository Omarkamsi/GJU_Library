"use client";
import { useState } from "react";
import type { Lang } from "@/lib/types";
import { T } from "@/lib/i18n";

export function ChatInput({ onSend, lang }: { onSend: (q: string) => void; lang: Lang }) {
  const [v, setV] = useState("");
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (v.trim()) {
          onSend(v);
          setV("");
        }
      }}
    >
      <input
        value={v}
        onChange={(e) => setV(e.target.value)}
        placeholder={T[lang].askPlaceholder}
        className="flex-1 border rounded px-3 py-2"
      />
      <button className="bg-black text-white rounded px-4 py-2">{T[lang].send}</button>
    </form>
  );
}
