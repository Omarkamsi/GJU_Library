import Image from "next/image";
import type { Lang } from "@/lib/types";

const T: Record<Lang, { title: string; sub: string; chips: string[] }> = {
  en: {
    title: "How can I help you today?",
    sub: "Hours, locations, databases, remote access — answered with citations from the library's own sources.",
    chips: [
      "Library hours",
      "How to access IEEE Xplore",
      "Where can I find Scopus",
      "Can I access the library from home?",
    ],
  },
  ar: {
    title: "كيف يمكنني مساعدتك؟",
    sub: "ساعات الدوام، المواقع، قواعد البيانات، الوصول عن بُعد — مع استشهادات من مصادر المكتبة.",
    chips: [
      "ساعات عمل المكتبة",
      "كيف أصل إلى IEEE Xplore",
      "أين أجد Scopus",
      "هل يمكنني الوصول للمكتبة من المنزل؟",
    ],
  },
  de: {
    title: "Wie kann ich helfen?",
    sub: "Öffnungszeiten, Standorte, Datenbanken, Fernzugriff — mit Belegen aus den Bibliotheksquellen.",
    chips: [
      "Öffnungszeiten",
      "Wie greife ich auf IEEE Xplore zu?",
      "Wo finde ich Scopus?",
      "Bibliothekszugriff von zu Hause?",
    ],
  },
};

export function EmptyState({
  lang,
  onPick,
}: {
  lang: Lang;
  onPick: (q: string) => void;
}) {
  const t = T[lang];
  return (
    <div className="flex flex-col items-center text-center gap-5 py-10">
      <Image
        src="/brand/gju-library-ai-empty.png"
        alt=""
        width={220}
        height={150}
        className="rounded-xl"
        priority
      />
      <div>
        <h2 className="text-2xl font-semibold text-gju-ink">{t.title}</h2>
        <p className="mt-2 text-sm text-gju-ink/60 max-w-md">{t.sub}</p>
      </div>
      <div className="flex flex-wrap justify-center gap-2 max-w-xl">
        {t.chips.map((c) => (
          <button
            key={c}
            onClick={() => onPick(c)}
            className="text-xs px-3 py-1.5 rounded-full bg-white border border-gju-ink/10 hover:border-gju-blue hover:text-gju-blue transition shadow-sm"
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
