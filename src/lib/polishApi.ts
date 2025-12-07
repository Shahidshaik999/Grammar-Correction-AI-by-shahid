// src/lib/polishApi.ts
// Helpers to talk to FastAPI backend

export type Mode = "grammar" | "professional" | "casual";
export type CorrectionMode = Mode;

export type ToneMode =
  | "friendly"
  | "professional"
  | "confident"
  | "calm"
  | "caring"
  | "persuasive";

export interface CorrectionResult {
  correctedText: string;
  changesSummary: string;
}

const API_BASE_URL = "http://localhost:8000";

// ---------- /correct ----------

export async function correctText(
  text: string,
  mode: Mode = "grammar"
): Promise<CorrectionResult> {
  const trimmed = text.trim();

  if (!trimmed) {
    return { correctedText: "", changesSummary: "" };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: trimmed, mode }),
    });

    if (!res.ok) {
      console.error("Backend /correct error:", res.status, res.statusText);
      return {
        correctedText: trimmed,
        changesSummary:
          "Could not reach grammar server – showing original text.",
      };
    }

    const data = await res.json();

    return {
      correctedText: data.correctedText ?? trimmed,
      changesSummary: data.changesSummary ?? "",
    };
  } catch (error) {
    console.error("Fetch error calling /correct:", error);
    return {
      correctedText: trimmed,
      changesSummary:
        "Error contacting grammar server – showing original text.",
    };
  }
}

// ---------- /polish-ai ----------

export async function polishAI(text: string): Promise<CorrectionResult> {
  const trimmed = text.trim();

  if (!trimmed) {
    return { correctedText: "", changesSummary: "" };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/polish-ai`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: trimmed }),
    });

    if (!res.ok) {
      console.error("Backend /polish-ai error:", res.status, res.statusText);
      return {
        correctedText: trimmed,
        changesSummary:
          "Could not reach AI server – showing original text.",
      };
    }

    const data = await res.json();

    return {
      correctedText: data.correctedText ?? trimmed,
      changesSummary: data.changesSummary ?? "AI fluent rewrite applied.",
    };
  } catch (error) {
    console.error("Fetch error calling /polish-ai:", error);
    return {
      correctedText: trimmed,
      changesSummary:
        "Error contacting AI server – showing original text.",
    };
  }
}

// ---------- /rewrite-tone (NEW) ----------

export async function rewriteTone(
  text: string,
  tone: ToneMode
): Promise<CorrectionResult> {
  const trimmed = text.trim();

  if (!trimmed) {
    return { correctedText: "", changesSummary: "" };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/rewrite-tone`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: trimmed, tone }),
    });

    if (!res.ok) {
      console.error("Backend /rewrite-tone error:", res.status, res.statusText);
      return {
        correctedText: trimmed,
        changesSummary:
          "Could not reach tone server – showing original text.",
      };
    }

    const data = await res.json();

    return {
      correctedText: data.correctedText ?? trimmed,
      changesSummary: data.changesSummary ?? `Tone '${tone}' applied.`,
    };
  } catch (error) {
    console.error("Fetch error calling /rewrite-tone:", error);
    return {
      correctedText: trimmed,
      changesSummary:
        "Error contacting tone server – showing original text.",
    };
  }
}

// Backwards compatible alias if some old code still uses polishText
export async function polishText(
  text: string,
  mode: Mode = "grammar"
): Promise<CorrectionResult> {
  return correctText(text, mode);
}
