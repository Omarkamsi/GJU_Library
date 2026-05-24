"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Segment } from "@/lib/types";
import { TrackedLink } from "./TrackedLink";
import { BookCard } from "./BookCard";

type Citation = { id: number; title: string | null; source: string };

export function AnswerSegments({
  segments,
  citations,
}: {
  segments: Segment[];
  citations?: Citation[];
}) {
  const byId = new Map((citations ?? []).map((c) => [c.id, c]));
  return (
    <>
      {segments.map((s, i) => {
        if (s.type === "text") {
          return (
            <ReactMarkdown
              key={i}
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => (
                  <span className="block">{children}</span>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside my-1 space-y-0.5">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside my-1 space-y-0.5">
                    {children}
                  </ol>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gju-blue underline decoration-dotted underline-offset-2"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {s.value}
            </ReactMarkdown>
          );
        }
        if (s.type === "book_card") {
          return <BookCard key={i} segment={s} />;
        }
        if (s.type === "passage_ref") {
          const c = byId.get(s.passage_id);
          const title = c ? c.title || c.source : `Passage ${s.passage_id}`;
          return (
            <sup
              key={i}
              className="inline-flex items-center mx-0.5 px-1.5 py-0.5 rounded-md text-[10px] font-mono bg-gju-blue-soft text-gju-blue ring-1 ring-gju-blue/10 cursor-help align-baseline"
              title={title}
            >
              P{s.passage_id}
            </sup>
          );
        }
        return <TrackedLink key={i} clickId={s.click_id} label={s.label} kind={s.kind} />;
      })}
    </>
  );
}
