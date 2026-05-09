export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: "include",
    headers: { "content-type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export type StreamEvent =
  | { type: "meta"; lang: string }
  | { type: "token"; text: string }
  | {
      type: "done";
      query_id: number;
      segments: any[];
      answer_text: string;
      citations: any[];
      suggested_databases: any[];
      lang: string;
      latency_ms: number;
    };

export async function streamChat(
  query: string,
  onEvent: (e: StreamEvent) => void,
): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    credentials: "include",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok || !res.body) throw new Error(`${res.status} ${await res.text()}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const frame = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const line = frame.startsWith("data: ") ? frame.slice(6) : frame;
      if (!line) continue;
      try {
        onEvent(JSON.parse(line) as StreamEvent);
      } catch {
        // ignore malformed frames
      }
    }
  }
}
