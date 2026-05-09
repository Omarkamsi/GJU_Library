"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { api, streamChat } from "@/lib/api";
import type { ChatResponse, Lang, Segment } from "@/lib/types";
import { dirOf } from "@/lib/i18n";
import { Header } from "./components/Header";
import { EmptyState } from "./components/EmptyState";
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
  const scrollAnchor = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api("/auth/me").catch(() => router.push("/login"));
  }, [router]);

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  async function send(query: string) {
    if (busy) return;
    setBusy(true);
    setTurns((t) => [
      ...t,
      { role: "user", text: query, lang },
      { role: "assistant", text: "", lang, streaming: true },
    ]);
    try {
      let buffer = "";
      await streamChat(query, (ev) => {
        if (ev.type === "meta") {
          setLang(ev.lang as Lang);
          setTurns((t) => {
            const c = [...t];
            c[c.length - 1] = { ...c[c.length - 1], lang: ev.lang as Lang };
            return c;
          });
        } else if (ev.type === "token") {
          buffer += ev.text;
          setTurns((t) => {
            const c = [...t];
            c[c.length - 1] = { ...c[c.length - 1], text: buffer };
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
        c[c.length - 1] = { role: "assistant", text: `Error: ${e.message}`, lang };
        return c;
      });
    } finally {
      setBusy(false);
    }
  }

  const isEmpty = turns.length === 0;

  return (
    <main
      className="min-h-screen flex flex-col bg-gju-paper"
      dir={dirOf(lang)}
    >
      <Header lang={lang} onLangChange={setLang} />

      <div className="flex-1 mx-auto w-full max-w-3xl px-4 pt-4 pb-32">
        {isEmpty ? (
          <EmptyState lang={lang} onPick={(q) => send(q)} />
        ) : (
          <div className="flex flex-col gap-4">
            {turns.map((t, i) => {
              const isPending =
                t.role === "assistant" && t.streaming && !t.text && !t.segments;
              return (
                <div key={i} className="space-y-1.5">
                  {isPending ? (
                    <div className="flex items-start gap-2.5">
                      <Image
                        src="/brand/gju-library-ai-avatar.png"
                        alt=""
                        width={32}
                        height={32}
                        className="rounded-full bg-white ring-1 ring-gju-ink/5"
                      />
                      <div className="rounded-2xl rounded-tl-md bg-white border border-gju-ink/5 px-4 py-3 shadow-bubble">
                        <span className="dot" />
                        <span className="dot ms-1" />
                        <span className="dot ms-1" />
                      </div>
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
                  {t.role === "assistant" && t.query_id && (
                    <div className="flex items-center gap-3">
                      <FeedbackPrompt queryId={t.query_id} lang={t.lang} />
                      {t.latency_ms != null && (
                        <span className="text-[10px] text-gju-ink/35 font-mono">
                          {(t.latency_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={scrollAnchor} />
          </div>
        )}
      </div>

      <div className="fixed bottom-0 inset-x-0 bg-gradient-to-t from-gju-paper via-gju-paper/95 to-transparent pt-6 pb-4 shadow-composer">
        <div className="mx-auto max-w-3xl px-4">
          <ChatInput onSend={send} lang={lang} busy={busy} />
        </div>
      </div>
    </main>
  );
}
