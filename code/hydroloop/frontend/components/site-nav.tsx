"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const LINKS = [
  { href: "/",          label: "Overview" },
  { href: "/wheel",     label: "Wheel" },
  { href: "/buildings", label: "Buildings" },
  { href: "/about",     label: "About" },
];

export function SiteNav() {
  const path = usePathname();
  const isActive = (href: string) =>
    href === "/" ? path === "/" : path === href || path.startsWith(href + "/");

  return (
    <nav className="sticky top-0 z-40 backdrop-blur bg-slate-950/70 border-b border-slate-800/80">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group rounded-lg px-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-water focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/gju-logo.png"
            alt="German Jordanian University"
            width={42}
            height={30}
            className="h-8 w-auto"
          />
          <span className="font-bold tracking-tight text-lg">
            <span className="text-water">Hydro</span><span className="text-energy">Loop</span>
          </span>
        </Link>

        <ul className="flex gap-1 text-sm">
          {LINKS.map(l => (
            <li key={l.href}>
              <Link
                href={l.href}
                className={clsx(
                  "px-3 py-2 rounded-lg transition-colors duration-200 ease-out",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-water focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
                  isActive(l.href)
                    ? "bg-slate-800/80 text-slate-100"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/60",
                )}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
