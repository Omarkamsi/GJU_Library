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
  const base = role === "assistant" ? "bg-white border" : "bg-neutral-100";
  return (
    <article className={`rounded-lg p-3 ${base}`} dir={dir}>
      {role === "assistant" && segments ? (
        <div className="leading-relaxed">
          <AnswerSegments segments={segments} />
        </div>
      ) : (
        <div className="whitespace-pre-wrap">{text}</div>
      )}
      {citations && citations.length > 0 && (
        <ul className="mt-2 text-xs text-neutral-500 list-disc ms-5">
          {citations.map((c) => (
            <li key={c.id}>
              [P{c.id}] {c.title || c.source}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
