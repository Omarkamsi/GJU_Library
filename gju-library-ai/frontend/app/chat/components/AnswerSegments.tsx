"use client";
import type { Segment } from "@/lib/types";
import { TrackedLink } from "./TrackedLink";

export function AnswerSegments({ segments }: { segments: Segment[] }) {
  return (
    <span>
      {segments.map((s, i) => {
        if (s.type === "text") return <span key={i}>{s.value}</span>;
        if (s.type === "passage_ref")
          return (
            <sup key={i} className="text-xs text-neutral-500">
              [P{s.passage_id}]
            </sup>
          );
        return <TrackedLink key={i} clickId={s.click_id} label={s.label} />;
      })}
    </span>
  );
}
