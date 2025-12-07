from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import os
import requests
import language_tool_python
from language_tool_python.exceptions import RateLimitError

# ---------------------------
# FastAPI app + CORS
# ---------------------------
app = FastAPI()

origins = [
    # Local dev
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # Deployed frontend (Vercel)
    "https://grammar-correction-ai-by-shahid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # for debugging you could use ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "TypePolish backend running"}


# ---------------------------
# Grammar tool (LanguageTool Public API)
# ---------------------------

# We use the PUBLIC API so we don't need Java or local server.
# Make it lazy + safe so rate limits don't crash the app.

_lt_tool = None  # cached client instance


def get_language_tool():
    """
    Lazily create/return LanguageToolPublicAPI client.

    If rate-limited or any other error occurs, return None.
    """
    global _lt_tool
    if _lt_tool is not None:
        return _lt_tool

    try:
        _lt_tool = language_tool_python.LanguageToolPublicAPI("en-US")
        return _lt_tool
    except RateLimitError:
        print("LanguageToolPublicAPI rate limit hit during init.")
        _lt_tool = None
        return None
    except Exception as e:
        print("LanguageToolPublicAPI init error:", e)
        _lt_tool = None
        return None


def apply_language_tool(text: str) -> str:
    """
    Basic grammar + spelling correction using LanguageToolPublicAPI.
    Falls back to original text if API not available.
    """
    tool = get_language_tool()
    cleaned = text.strip()
    if not cleaned:
        return ""

    if tool is None:
        # No tool available (rate limit / network) – just return original
        return cleaned

    try:
        matches = tool.check(cleaned)
        corrected = language_tool_python.utils.correct(cleaned, matches)
        return corrected.strip()
    except RateLimitError:
        print("LanguageToolPublicAPI rate limit hit during check().")
        return cleaned
    except Exception as e:
        print("LanguageToolPublicAPI error:", e)
        return cleaned


# ---------------------------
# Hugging Face config (Smart Rewrite v3)
# ---------------------------

HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # set this in hosting env


def build_hf_prompt(text: str, tone: str, style: str) -> str:
    """
    Build instruction prompt for a text2text model (Flan-T5 style).
    """
    tone_instruction_map = {
        "friendly": "in a warm, friendly tone",
        "professional": "in a clear and professional tone",
        "confident": "in a confident, self-assured tone",
        "calm": "in a calm and composed tone",
        "caring": "in a caring and supportive tone",
        "persuasive": "in a persuasive and encouraging tone",
        "neutral": "in a neutral tone",
    }

    style_instruction_map = {
        "neutral": "with normal everyday English",
        "student": "with simple, clear English suitable for a college student",
        "corporate": "with formal business email style",
        "ielts": "with IELTS-style academic English",
        "romantic": "with soft and gentle wording, but still respectful",
    }

    tone_part = tone_instruction_map.get(tone, "in a neutral tone")
    style_part = style_instruction_map.get(style, "with normal everyday English")

    instruction = (
        f"Paraphrase the following text {tone_part} and {style_part}. "
        "Keep the original meaning and person the same. "
        "Use natural, fluent sentences and split long sentences if needed.\n\n"
        f"Text: {text}\n\n"
        "Rewritten:"
    )
    return instruction


def call_hf_rewrite(prompt: str, fallback: str) -> tuple[str, bool]:
    """
    Call Hugging Face Inference API.
    Returns (text, used_hf) where used_hf=False means we fell back.
    """
    if not HF_API_TOKEN:
        print("HF_API_TOKEN not set; using fallback text.")
        return fallback, False

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=40)
        resp.raise_for_status()
        data = resp.json()

        generated = None
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            generated = data[0].get("generated_text")
        elif isinstance(data, dict) and "generated_text" in data:
            generated = data["generated_text"]

        if not generated:
            print("HF response format unexpected, using fallback.")
            return fallback, False

        text = generated.strip()
        lower = text.lower()

        # Cut off instructions if model echoes them
        if "rewritten:" in lower:
            idx = lower.rfind("rewritten:")
            text = text[idx + len("rewritten:") :].strip()
        elif "text:" in lower:
            idx = lower.rfind("text:")
            tail = text[idx + len("text:") :].strip()
            if 0 < len(tail) < len(text):
                text = tail

        text = " ".join(text.split())
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."

        if not text:
            return fallback, False

        return text, True

    except Exception as e:
        print("Hugging Face API error:", e)
        return fallback, False


# ---------------------------
# Request models
# ---------------------------


class TextRequest(BaseModel):
    text: str
    mode: Optional[str] = "grammar"  # "grammar" | "professional" | "casual"


class AIRewriteRequest(BaseModel):
    text: str
    tone: Optional[str] = "friendly"  # friendly | professional | confident | calm | caring | persuasive | neutral
    style: Optional[str] = "neutral"  # neutral | student | corporate | ielts | romantic


# ---------------------------
# Core functions
# ---------------------------


def basic_tone_adjust(text: str, mode: str) -> str:
    """
    Very light tone adjust for /correct endpoint.
    """
    updated = text

    if mode == "professional":
        replacements = {
            " bro": " sir",
            " gonna": " going to",
            " wanna": " want to",
            " don't": " do not",
            " can't": " cannot",
            " won't": " will not",
            " okay": " all right",
            " ok": " all right",
        }
        for w, r in replacements.items():
            updated = updated.replace(w, r)

    elif mode == "casual":
        replacements = {
            "sir": "bro",
            "madam": "bro",
        }
        for w, r in replacements.items():
            updated = updated.replace(w, r)

    return updated


def simple_correct(text: str, mode: str = "grammar"):
    """
    Grammar + spelling correction + light tone.
    """
    cleaned = text.strip()
    if not cleaned:
        return "", "No text provided."

    corrected = apply_language_tool(cleaned)
    corrected = basic_tone_adjust(corrected, mode)

    if corrected:
        corrected = corrected[0].upper() + corrected[1:]

    if corrected and corrected[-1] not in ".!?":
        corrected += "."

    summary = f"Grammar and spelling corrected using LanguageToolPublicAPI with {mode} style."
    return corrected, summary


# ---------------------------
# Routes
# ---------------------------


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


@app.post("/polish-ai")
def polish_ai(body: AIRewriteRequest):
    """
    Smart Rewrite v3:
    1) Grammar pass
    2) AI paraphrase with tone + style via Hugging Face
    """
    raw = body.text.strip()
    if not raw:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    grammared, _ = simple_correct(raw, "grammar")

    tone = (body.tone or "friendly").lower()
    style = (body.style or "neutral").lower()

    prompt = build_hf_prompt(grammared, tone, style)
    rewritten, used_hf = call_hf_rewrite(prompt, fallback=grammared)

    tone_label = tone.capitalize()
    style_label = style.capitalize()

    if used_hf:
        summary = (
            f"Expression adjusted using Smart Rewrite v3 (Hugging Face) "
            f"with '{tone_label}' tone and '{style_label}' writing style."
        )
    else:
        summary = (
            "Basic rewrite applied using grammar correction only; "
            f"Hugging Face model was not available. Tone: '{tone_label}', Style: '{style_label}'."
        )

    return {
        "correctedText": rewritten,
        "changesSummary": summary,
        "appliedTone": tone,
        "appliedStyle": style,
    }
