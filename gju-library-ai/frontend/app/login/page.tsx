"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { T } from "@/lib/i18n";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify({ email }) });
      router.push("/chat");
    } catch (x: any) {
      setErr(String(x.message || x));
    }
  }

  return (
    <main className="mx-auto max-w-sm p-8">
      <h1 className="text-2xl font-semibold mb-6">GJU Library AI</h1>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm">{T.en.emailLabel}</label>
        <input
          type="email" required value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="you@gju.edu.jo"
        />
        <button className="w-full bg-black text-white rounded px-3 py-2">{T.en.login}</button>
        {err && <p className="text-red-600 text-sm">{err}</p>}
      </form>
      <p className="text-xs text-neutral-500 mt-6">
        M0 dev login. Entra ID SSO replaces this in a later milestone.
      </p>
    </main>
  );
}
