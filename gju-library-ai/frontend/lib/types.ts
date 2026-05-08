export type Lang = "en" | "ar" | "de";

export type Segment =
  | { type: "text"; value: string }
  | { type: "passage_ref"; passage_id: number }
  | {
      type: "link";
      click_id: string;
      label: string;
      kind: "database" | "external";
      ref: string | null;
    };

export type ChatResponse = {
  query_id: number;
  segments: Segment[];
  answer_text: string;
  citations: { id: number; title: string | null; source: string }[];
  suggested_databases: { slug: string; name: string }[];
  lang: Lang;
  latency_ms: number;
};
