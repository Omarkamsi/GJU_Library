"use client";
import { useEffect, useRef } from "react";
import type { Reading } from "./types";
import { apiBase } from "./api";

export function useReadingStream(onReading: (r: Reading) => void) {
  const cb = useRef(onReading);
  cb.current = onReading;
  useEffect(() => {
    let es: EventSource | null = null;
    let backoff = 500, alive = true;
    const open = () => {
      es = new EventSource(`${apiBase}/api/stream`);
      es.addEventListener("reading", (e) => {
        try { cb.current(JSON.parse((e as MessageEvent).data)); } catch {}
      });
      es.onerror = () => {
        es?.close();
        if (alive) {
          setTimeout(open, backoff);
          backoff = Math.min(backoff * 2, 15000);
        }
      };
      es.onopen = () => { backoff = 500; };
    };
    open();
    return () => { alive = false; es?.close(); };
  }, []);
}
