"use client";
type Props = { clickId: string; label: string; apiBase?: string };

export function TrackedLink({ clickId, label, apiBase = "/api" }: Props) {
  return (
    <a
      href={`${apiBase}/go/${encodeURIComponent(clickId)}`}
      target="_blank"
      rel="noopener noreferrer"
      className="underline decoration-dotted"
    >
      {label}
    </a>
  );
}
