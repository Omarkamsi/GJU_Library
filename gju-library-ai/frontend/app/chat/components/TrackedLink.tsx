"use client";
type Props = {
  clickId: string;
  label: string;
  kind?: "database" | "external";
  apiBase?: string;
};

export function TrackedLink({ clickId, label, kind = "external", apiBase = "/api" }: Props) {
  const isDb = kind === "database";
  const cls = isDb
    ? "inline-flex items-center gap-1 px-2 py-0.5 mx-0.5 rounded-md text-[12px] font-medium bg-gju-gold-soft text-gju-ink ring-1 ring-gju-gold/40 hover:bg-gju-gold/30 transition"
    : "underline decoration-dotted decoration-gju-blue/40 underline-offset-2 hover:decoration-gju-blue text-gju-blue";
  return (
    <a
      href={`${apiBase}/go/${encodeURIComponent(clickId)}`}
      target="_blank"
      rel="noopener noreferrer"
      className={cls}
    >
      {isDb && (
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v6c0 1.7 4 3 9 3s9-1.3 9-3V5" />
          <path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6" />
        </svg>
      )}
      {label}
    </a>
  );
}
