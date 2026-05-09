"use client";
import type { Segment } from "@/lib/types";
import { TrackedLink } from "./TrackedLink";

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
    <span>
      {segments.map((s, i) => {
        if (s.type === "text") return <span key={i}>{s.value}</span>;
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
    </span>
  );
}
