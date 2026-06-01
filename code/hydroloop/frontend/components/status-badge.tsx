import clsx from "clsx";
import { fmtRelative } from "@/lib/format";

export function StatusBadge({ lastSeen }: { lastSeen: string | null }) {
  const ageSec = lastSeen ? (Date.now() - new Date(lastSeen).getTime()) / 1000 : Infinity;
  const live = ageSec < 60;
  const tone = live ? "bg-emerald-500"
             : ageSec < 300 ? "bg-amber-500"
             : "bg-rose-500";
  return (
    <span className="inline-flex items-center gap-2 text-xs text-slate-400">
      <span className="relative inline-flex h-2 w-2">
        {live && (
          <span className="absolute inset-0 rounded-full bg-emerald-500 opacity-75 animate-ping motion-reduce:hidden" />
        )}
        <span className={clsx("relative h-2 w-2 rounded-full", tone)} />
      </span>
      {fmtRelative(lastSeen)}
    </span>
  );
}
