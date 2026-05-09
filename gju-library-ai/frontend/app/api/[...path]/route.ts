import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE ?? "http://backend:8080";

async function proxy(req: NextRequest, ctx: { params: { path: string[] } }) {
  const path = ctx.params.path.join("/");
  const url = `${BACKEND}/${path}${req.nextUrl.search}`;
  const headers = new Headers(req.headers);
  headers.set("host", new URL(BACKEND).host);
  const init: RequestInit & { duplex?: string } = {
    method: req.method,
    headers,
    body: ["GET", "HEAD"].includes(req.method) ? undefined : await req.text(),
    redirect: "manual",
    cache: "no-store",
  };
  const upstream = await fetch(url, init);
  const res = new NextResponse(upstream.body, { status: upstream.status });
  upstream.headers.forEach((v, k) => {
    if (k.toLowerCase() === "set-cookie") res.headers.append("set-cookie", v);
    else res.headers.set(k, v);
  });
  res.headers.set("X-Accel-Buffering", "no");
  return res;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
