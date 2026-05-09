import Image from "next/image";
import type { Lang, Segment } from "@/lib/types";
import { dirOf } from "@/lib/i18n";
import { AnswerSegments } from "./AnswerSegments";

type Props = {
  role: "user" | "assistant";
  text?: string;
  segments?: Segment[];
  lang: Lang;
  citations?: { id: number; title: string | null; source: string }[];
};

export function ChatMessage({ role, text, segments, lang, citations }: Props) {
  const dir = dirOf(lang);
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end" dir={dir}>
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-gju-blue text-white px-4 py-2.5 shadow-bubble whitespace-pre-wrap text-[15px] leading-relaxed">
          {text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5" dir={dir}>
      <div className="shrink-0 mt-0.5">
        <Image
          src="/brand/gju-library-ai-avatar.png"
          alt=""
          width={32}
          height={32}
          className="rounded-full ring-1 ring-gju-ink/5 bg-white"
        />
      </div>
      <article className="flex-1 max-w-[85%] rounded-2xl rounded-tl-md bg-white border border-gju-ink/5 px-4 py-3 shadow-bubble">
        <div className="text-[15px] leading-relaxed text-gju-ink">
          {segments ? (
            <AnswerSegments segments={segments} citations={citations} />
          ) : (
            <span className="whitespace-pre-wrap">{text}</span>
          )}
        </div>
        {citations && citations.length > 0 && (
          <details className="mt-2 group">
            <summary className="text-[11px] text-gju-ink/45 cursor-pointer select-none hover:text-gju-blue">
              {citations.length} {citations.length === 1 ? "source" : "sources"}
            </summary>
            <ul className="mt-2 space-y-1">
              {citations.map((c) => (
                <li key={c.id} className="text-[11px] text-gju-ink/55 flex gap-2">
                  <span className="font-mono text-gju-blue">[P{c.id}]</span>
                  <span>{c.title || c.source}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </article>
    </div>
  );
}
