"use client";
import Image from "next/image";
import Link from "next/link";
import type { Lang } from "@/lib/types";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

const labels: Record<Lang, { en: string; ar: string; de: string; tagline: string; signOut: string }> = {
  en: { en: "EN", ar: "AR", de: "DE", tagline: "Library assistant — ask in any language",  signOut: "Sign out" },
  ar: { en: "EN", ar: "AR", de: "DE", tagline: "مساعد المكتبة — اسأل بأي لغة",                signOut: "تسجيل خروج" },
  de: { en: "EN", ar: "AR", de: "DE", tagline: "Bibliotheks-Assistenz — frag in jeder Sprache", signOut: "Abmelden" },
};

export function Header({
  lang,
  onLangChange,
}: {
  lang: Lang;
  onLangChange: (l: Lang) => void;
}) {
  const router = useRouter();
  const t = labels[lang];

  async function signOut() {
    try { await api("/auth/logout", { method: "POST" }); } catch {}
    router.push("/login");
  }

  const tab = (l: Lang, label: string) => (
    <button
      key={l}
      onClick={() => onLangChange(l)}
      className={
        "px-2.5 py-1 text-xs font-medium rounded-full transition " +
        (l === lang
          ? "bg-gju-blue text-white shadow-sm"
          : "text-gju-ink/60 hover:text-gju-ink hover:bg-white")
      }
      aria-pressed={l === lang}
    >
      {label}
    </button>
  );

  return (
    <header className="sticky top-0 z-10 bg-gju-paper/85 backdrop-blur border-b border-gju-ink/5">
      <div className="mx-auto max-w-3xl px-4 py-3 flex items-center gap-3">
        <Image
          src="/brand/gju-logo.png"
          alt="GJU"
          width={36}
          height={36}
          priority
          className="rounded-md"
        />
        <div className="flex-1 leading-tight">
          <div className="font-semibold text-gju-ink">GJU Library AI</div>
          <div className="text-[11px] text-gju-ink/55">{t.tagline}</div>
        </div>
        <div className="flex items-center gap-1 bg-gju-blue-soft rounded-full p-1">
          {tab("en", t.en)}
          {tab("ar", t.ar)}
          {tab("de", t.de)}
        </div>
        <Link
          href="/admin"
          className="text-xs text-gju-ink/55 hover:text-gju-blue"
          title="Admin"
        >
          Admin
        </Link>
        <button
          onClick={signOut}
          className="text-xs text-gju-ink/55 hover:text-gju-ink"
          title={t.signOut}
        >
          {t.signOut}
        </button>
      </div>
    </header>
  );
}
