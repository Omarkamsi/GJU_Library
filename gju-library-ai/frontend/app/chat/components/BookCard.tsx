import type { BookCardSegment } from "@/lib/types";

type Props = {
  segment: BookCardSegment;
};

export function BookCard({ segment }: Props) {
  return (
    <div className="rounded-xl border border-gju-ink/10 bg-white overflow-hidden my-2 shadow-sm">
      {/* Title header */}
      <div className="border-b border-gju-ink/10 px-4 py-3 bg-gju-blue/5">
        <p className="font-semibold text-gju-ink text-[14px] leading-snug">
          📖 {segment.title}
        </p>
      </div>

      {/* Fields */}
      <div className="px-4 py-3 space-y-1.5 text-[13px] text-gju-ink/80">
        {segment.author && (
          <p>
            <span className="font-medium text-gju-ink">✍️ Author:</span>{" "}
            {segment.author}
          </p>
        )}
        {segment.genre && (
          <p>
            <span className="font-medium text-gju-ink">🏷️ Genre / Subject:</span>{" "}
            {segment.genre}
          </p>
        )}
        {segment.call_number && (
          <p>
            <span className="font-medium text-gju-ink">🔢 Call Number:</span>{" "}
            {segment.call_number}
          </p>
        )}
        {segment.year && (
          <p>
            <span className="font-medium text-gju-ink">📅 Year:</span>{" "}
            {segment.year}
          </p>
        )}
      </div>

      {/* OPAC link */}
      <div className="px-4 pb-3">
        <a
          href={`/api/go/${encodeURIComponent(segment.click_id)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium bg-gju-blue text-white hover:bg-gju-blue/90 transition-colors"
        >
          Check availability &amp; shelf location →
        </a>
      </div>

      {/* Passage citation chips */}
      {segment.passage_ids.length > 0 && (
        <div className="px-4 pb-2 flex gap-1 flex-wrap">
          {segment.passage_ids.map((pid) => (
            <sup
              key={pid}
              className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-mono bg-gju-blue-soft text-gju-blue ring-1 ring-gju-blue/10"
            >
              P{pid}
            </sup>
          ))}
        </div>
      )}
    </div>
  );
}
