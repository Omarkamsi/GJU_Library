import type { Lang } from "./types";

export const dirOf = (l: Lang): "ltr" | "rtl" => (l === "ar" ? "rtl" : "ltr");

export const T: Record<Lang, Record<string, string>> = {
  en: {
    send: "Send", helpful: "Was this helpful?", yes: "Yes", no: "No", skip: "Skip",
    login: "Sign in", emailLabel: "GJU email",
    askPlaceholder: "What are the library hours?",
  },
  ar: {
    send: "إرسال", helpful: "هل كان هذا مفيدًا؟", yes: "نعم", no: "لا", skip: "تخطّي",
    login: "تسجيل الدخول", emailLabel: "البريد الجامعي",
    askPlaceholder: "ما هي ساعات الدوام؟",
  },
  de: {
    send: "Senden", helpful: "War das hilfreich?", yes: "Ja", no: "Nein", skip: "Überspringen",
    login: "Anmelden", emailLabel: "GJU-E-Mail",
    askPlaceholder: "Wie sind die Öffnungszeiten?",
  },
};
