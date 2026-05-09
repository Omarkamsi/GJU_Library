"use client";
import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      router.push("/chat");
    } catch (x: any) {
      setErr(String(x.message || x));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen grid grid-cols-1 md:grid-cols-2 bg-gju-paper">
      <div className="hidden md:flex items-center justify-center bg-gju-blue-soft bg-grid">
        <Image
          src="/brand/gju-library-ai-hero.png"
          alt=""
          width={520}
          height={420}
          priority
          className="rounded-2xl shadow-bubble"
        />
      </div>
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-3 mb-6">
            <Image
              src="/brand/gju-logo.png"
              alt="GJU"
              width={44}
              height={44}
              className="rounded-md"
              priority
            />
            <div className="leading-tight">
              <div className="text-lg font-semibold">GJU Library AI</div>
              <div className="text-xs text-gju-ink/55">
                Sign in with your university email
              </div>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <label className="block text-xs font-medium text-gju-ink/70">
              GJU email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border border-gju-ink/10 rounded-xl px-3 py-2.5 text-[15px] focus:border-gju-blue"
              placeholder="you@gju.edu.jo"
              autoFocus
            />
            <button
              disabled={busy || !email.trim()}
              className="w-full bg-gju-blue text-white rounded-xl px-3 py-2.5 font-medium hover:bg-gju-ink transition disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Continue"}
            </button>
            {err && (
              <p className="text-red-600 text-xs bg-red-50 border border-red-100 rounded-md px-2 py-1.5">
                {err}
              </p>
            )}
          </form>

          <p className="text-[11px] text-gju-ink/45 mt-6 leading-relaxed">
            M0 dev login — replaces with university SSO in a later milestone.
            Your email is not stored; only a hashed identifier.
          </p>
        </div>
      </div>
    </main>
  );
}
