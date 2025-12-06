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

// 🔴 Use your deployed backend URL here
const BACKEND_BASE = "https://grammar-correction-ai-by-shahid.onrender.com";
// For local testing, you can temporarily change this back to:
// const BACKEND_BASE = "http://localhost:8000";

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

    const data = await res.json();
    return data as {
      correctedText: string;
      changesSummary: string;
    };
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

    const data = await res.json();
    return data as {
      correctedText: string;
      changesSummary: string;
    };
  } catch (err) {
    console.error("Fetch /polish-ai error:", err);
    return null;
  }
}
