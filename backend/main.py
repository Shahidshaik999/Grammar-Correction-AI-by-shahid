from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import os
import requests
import language_tool_python

app = FastAPI()

# ---------- CORS ----------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # deployed frontend (add yours here)
    "https://grammar-correction-ai-by-shahid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Root ----------
@app.get("/")
def read_root():
    return {"message": "TypePolish backend running"}


# ---------- Grammar Tool ----------
tool = language_tool_python.LanguageTool("en-US")


# ---------- Hugging Face paraphrase model (remote) ----------

# You can change this if you want another model later
HF_API_URL = "https://api-inference.huggingface.co/models/Vamsi/T5_Paraphrase_Paws"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # set this in Render / server env, NOT in code


def generate_paraphrase(text: str, prompt_prefix: str) -> str:
    """
    Helper to generate paraphrase with a certain prompt style,
    using Hugging Face Inference API instead of local T5.
    """
    base = text.strip()
    if not base:
        return ""

    # If token not configured, just return the original text
    if not HF_API_TOKEN:
        print("HF_API_TOKEN not set; returning original text.")
        return base

    full_input = f"{prompt_prefix} {base}"

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": full_input}

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=40)
        resp.raise_for_status()
        data = resp.json()

        # Typical HF text2text output: [{"generated_text": "..."}]
        generated = None
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            generated = data[0].get("generated_text")
        elif isinstance(data, dict) and "generated_text" in data:
            generated = data["generated_text"]

        if not generated:
            print("Unexpected HF response format, falling back to original.")
            return base

        out = generated.strip()
        # Basic cleanup
        out = " ".join(out.split())
        if out and out[0].isalpha():
            out = out[0].upper() + out[1:]
        if out and out[-1] not in ".!?":
            out += "."

        return out or base
    except Exception as e:
        print("Hugging Face API error:", e)
        # On error, fall back to original text
        return base


# ---------- Request Models ----------

class TextRequest(BaseModel):
    text: str
    mode: Optional[str] = "grammar"  # "grammar" | "professional" | "casual"


class AIRequest(BaseModel):
    text: str


class ToneRequest(BaseModel):
    text: str
    tone: str  # "friendly" | "professional" | "confident" | "calm" | "caring" | "persuasive"


# ---------- Core Grammar Correction ----------

def simple_correct(text: str, mode: str = "grammar"):
    updated = text.strip()
    if not updated:
        return "", "No text provided."

    # 1) Grammar + spelling correction using LanguageTool
    matches = tool.check(updated)
    updated = language_tool_python.utils.correct(updated, matches)

    # 2) Capitalize first letter
    updated = updated.strip()
    if updated:
        updated = updated[0].upper() + updated[1:]

    # 3) Ensure ending punctuation
    if updated and updated[-1] not in ".!?":
        updated += "."

    # 4) Tone changes (very light rules)
    if mode == "professional":
        pro_replacements = {
            " bro": " sir",
            " gonna": " going to",
            " wanna": " want to",
            " pls": " please",
            " don't": " do not",
            " can't": " cannot",
        }
        for wrong, right in pro_replacements.items():
            updated = updated.replace(wrong, right)

    elif mode == "casual":
        updated = updated.replace(" sir", " bro")

    summary = f"Grammar and spelling corrected using LanguageTool with {mode} style."

    return updated, summary


# ---------- /correct ----------

@app.post("/correct")
def correct_text(body: TextRequest):
    text = body.text.strip()
    if not text:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    corrected, summary = simple_correct(text, body.mode or "grammar")

    return {
        "correctedText": corrected,
        "changesSummary": summary,
    }


# ---------- /polish-ai (fluent rewrite) ----------

@app.post("/polish-ai")
def polish_ai(body: AIRequest):
    base = body.text.strip()
    if not base:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    # Step 1: grammar
    corrected, _ = simple_correct(base, "grammar")

    # Step 2: fluent paraphrase via Hugging Face
    fluent = generate_paraphrase(
        corrected,
        "paraphrase this to be more clear and fluent:",
    )

    return {
        "correctedText": fluent,
        "changesSummary": "Grammar and spelling corrected, then paraphrased using Hugging Face for more fluent English.",
    }


# ---------- /rewrite-tone ----------

TONE_PROMPTS = {
    "friendly": "paraphrase this in a warm and friendly tone:",
    "professional": "paraphrase this in a polite and professional tone:",
    "confident": "paraphrase this in a confident and assertive tone:",
    "calm": "paraphrase this in a calm and respectful tone, softening any anger:",
    "caring": "paraphrase this in a caring and supportive tone:",
    "persuasive": "paraphrase this in a clear and persuasive tone:",
}


@app.post("/rewrite-tone")
def rewrite_tone(body: ToneRequest):
    base = body.text.strip()
    if not base:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    tone_key = body.tone.lower()
    prompt = TONE_PROMPTS.get(
        tone_key,
        "paraphrase this clearly and naturally:",
    )

    toned_text = generate_paraphrase(base, prompt)

    return {
        "correctedText": toned_text,
        "changesSummary": f"Expression improved using AI with '{tone_key}' tone.",
    }
