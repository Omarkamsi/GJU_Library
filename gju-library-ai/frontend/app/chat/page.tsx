"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ChatResponse, Lang, Segment } from "@/lib/types";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { FeedbackPrompt } from "./components/FeedbackPrompt";

type Turn = {
  role: "user" | "assistant";
  text?: string;
  segments?: Segment[];
  lang: Lang;
  query_id?: number;
  citations?: ChatResponse["citations"];
};

export default function ChatPage() {
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    api("/auth/me").catch(() => router.push("/login"));
  }, [router]);

  async function send(query: string) {
    setBusy(true);
    setTurns((t) => [...t, { role: "user", text: query, lang }]);
    try {
      const r = await api<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setLang(r.lang);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          segments: r.segments,
          query_id: r.query_id,
          citations: r.citations,
          lang: r.lang,
        },
      ]);
    } catch (e: any) {
      setTurns((t) => [...t, { role: "assistant", text: `Error: ${e.message}`, lang }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6 flex flex-col gap-4 min-h-screen">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">GJU Library AI</h1>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="en">English</option>
          <option value="ar">العربية</option>
          <option value="de">Deutsch</option>
        </select>
      </header>
      <div className="flex-1 flex flex-col gap-3">
        {turns.map((t, i) => (
          <div key={i} className="space-y-1">
            <ChatMessage
              role={t.role}
              segments={t.segments}
              text={t.text}
              lang={t.lang}
              citations={t.citations}
            />
            {t.role === "assistant" && t.query_id && (
              <FeedbackPrompt queryId={t.query_id} lang={t.lang} />
            )}
          </div>
        ))}
        {busy && <p className="text-sm text-neutral-500">…</p>}
      </div>
      <div className="sticky bottom-0 bg-white pt-2">
        <ChatInput onSend={send} lang={lang} />
      </div>
    </main>
  );
}
