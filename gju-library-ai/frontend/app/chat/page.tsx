"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, streamChat } from "@/lib/api";
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
  streaming?: boolean;
  latency_ms?: number;
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
    setTurns((t) => [
      ...t,
      { role: "user", text: query, lang },
      { role: "assistant", text: "", lang, streaming: true },
    ]);

    try {
      let assistantBuffer = "";
      await streamChat(query, (ev) => {
        if (ev.type === "meta") {
          setLang(ev.lang as Lang);
          setTurns((t) => {
            const c = [...t];
            c[c.length - 1] = { ...c[c.length - 1], lang: ev.lang as Lang };
            return c;
          });
        } else if (ev.type === "token") {
          assistantBuffer += ev.text;
          setTurns((t) => {
            const c = [...t];
            c[c.length - 1] = { ...c[c.length - 1], text: assistantBuffer };
            return c;
          });
        } else if (ev.type === "done") {
          setTurns((t) => {
            const c = [...t];
            c[c.length - 1] = {
              role: "assistant",
              segments: ev.segments as Segment[],
              query_id: ev.query_id,
              citations: ev.citations,
              lang: ev.lang as Lang,
              latency_ms: ev.latency_ms,
            };
            return c;
          });
        }
      });
    } catch (e: any) {
      setTurns((t) => {
        const c = [...t];
        c[c.length - 1] = {
          role: "assistant",
          text: `Error: ${e.message}`,
          lang,
        };
        return c;
      });
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
        {turns.map((t, i) => {
          const isPending =
            t.role === "assistant" && t.streaming && !t.text && !t.segments;
          return (
            <div key={i} className="space-y-1">
              {isPending ? (
                <div className="flex items-center gap-2 text-sm text-neutral-500">
                  <span className="inline-flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: "120ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-bounce" style={{ animationDelay: "240ms" }} />
                  </span>
                  thinking…
                </div>
              ) : (
                <ChatMessage
                  role={t.role}
                  segments={t.segments}
                  text={t.text}
                  lang={t.lang}
                  citations={t.citations}
                />
              )}
              {t.role === "assistant" && t.latency_ms != null && (
                <p className="text-xs text-neutral-400">{(t.latency_ms / 1000).toFixed(1)}s</p>
              )}
              {t.role === "assistant" && t.query_id && (
                <FeedbackPrompt queryId={t.query_id} lang={t.lang} />
              )}
            </div>
          );
        })}
      </div>
      <div className="sticky bottom-0 bg-white pt-2">
        <ChatInput onSend={send} lang={lang} />
      </div>
    </main>
  );
}
