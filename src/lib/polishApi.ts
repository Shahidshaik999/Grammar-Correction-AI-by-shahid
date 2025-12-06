export type Mode = "grammar" | "professional" | "casual";

export type ToneMode =
  | "friendly"
  | "professional"
  | "confident"
  | "calm"
  | "caring"
  | "persuasive"
  | "neutral";

export type StyleProfile =
  | "neutral"
  | "student"
  | "corporate"
  | "ielts"
  | "romantic";

type PolishResponse = {
  correctedText: string;
  changesSummary: string;
  appliedTone?: string;
  appliedStyle?: string;
};

// Use env var in production, fall back to localhost in dev
const BACKEND_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function polishText(text: string, mode: Mode = "grammar") {
  try {
    const res = await fetch(`${BACKEND_BASE}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mode }),
    });

    if (!res.ok) {
      console.error("Backend /correct error:", res.status);
      return null;
    }

    const data = (await res.json()) as PolishResponse;
    return data;
  } catch (err) {
    console.error("Fetch /correct error:", err);
    return null;
  }
}

export async function polishWithAI(
  text: string,
  tone: ToneMode = "friendly",
  style: StyleProfile = "neutral"
) {
  try {
    const res = await fetch(`${BACKEND_BASE}/polish-ai`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, tone, style }),
    });

    if (!res.ok) {
      console.error("Backend /polish-ai error:", res.status);
      return null;
    }

    const data = (await res.json()) as PolishResponse;
    return data;
  } catch (err) {
    console.error("Fetch /polish-ai error:", err);
    return null;
  }
}
