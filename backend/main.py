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
    allow_origins=origins,  # for testing, you could temporarily use ["*"]
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

_lt_tool = None  # cached instance


def get_language_tool():
    """
    Lazily create the LanguageToolPublicAPI client.

    If rate-limited or any error occurs, return None so that
    the backend still runs and deploy never fails.
    """
    global _lt_tool
    if _lt_tool is not None:
        return _lt_tool

    try:
        _lt_tool = language_tool_python.LanguageToolPublicAPI("en-US")
        return _lt_tool
    except RateLimitError as e:
        print("LanguageToolPublicAPI rate limit:", e)
        _lt_tool = None
        return None
    except Exception as e:
        print("LanguageToolPublicAPI error:", e)
        _lt_tool = None
        return None


# ---------------------------
# Hugging Face config (for rewrite)
# ---------------------------

# You can change the model later if you want
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")


def build_hf_prompt(text: str, tone: str, style: str) -> str:
    """
    Build the same style of instruction you used for Smart Rewrite v3,
    but now for a Hugging Face text2text model.
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


def call_hf_rewrite(prompt: str) -> str:
    """
    Calls Hugging Face Inference API with the given prompt.
    Falls back gracefully if something goes wrong.
    """
    # If token not set, just return prompt tail (so app doesn't crash)
    if not HF_API_TOKEN:
        print("HF_API_TOKEN not set; returning prompt as fallback.")
        return prompt

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # For text2text models, HF usually returns a list of dicts with "generated_text"
        generated = None
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            generated = data[0].get("generated_text")
        elif isinstance(data, dict) and "generated_text" in data:
            generated = data["generated_text"]

        if not generated:
            generated = str(data)

        text = generated.strip()

        # Remove a possible "Rewritten:" prefix
        if text.lower().startswith("rewritten:"):
            text = text[len("rewritten:") :].strip()

        # Basic cleanup
        text = " ".join(text.split())
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."

        return text
    except Exception as e:
        print("Hugging Face API error:", e)
        # Fallback: return original prompt on error so endpoint still works
        return prompt


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
    Very light tone adjust for /correct endpoint
    (keep this simple, most magic comes from AI endpoint).
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
    Uses LanguageToolPublicAPI when available, falls back gracefully otherwise.
    """
    cleaned = text.strip()
    if not cleaned:
        return "", "No text provided."

    lt_used = False
    tool = get_language_tool()

    corrected = cleaned
    if tool is not None:
        try:
            matches = tool.check(cleaned)
            corrected = language_tool_python.utils.correct(cleaned, matches)
            lt_used = True
        except RateLimitError as e:
            print("LanguageToolPublicAPI rate limit during check:", e)
            lt_used = False
        except Exception as e:
            print("LanguageToolPublicAPI error during check:", e)
            lt_used = False

    corrected = basic_tone_adjust(corrected, mode)

    # Capitalize first letter
    corrected = corrected.strip()
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]

    # Ensure punctuation
    if corrected and corrected[-1] not in ".!?":
        corrected += "."

    if lt_used:
        summary = f"Grammar and spelling corrected using LanguageToolPublicAPI with {mode} style."
    else:
        summary = (
            f"Basic cleanup applied with {mode} style. "
            "LanguageToolPublicAPI was not available (rate limit or network error)."
        )

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

    # Step 1 – basic grammar cleanup first
    grammared, _ = simple_correct(raw, "grammar")

    # Step 2 – AI paraphrase with tone + style
    tone = (body.tone or "friendly").lower()
    style = (body.style or "neutral").lower()

    prompt = build_hf_prompt(grammared, tone, style)
    rewritten = call_hf_rewrite(prompt)

    # Build human-readable summary
    tone_label = tone.capitalize()
    style_label = style.capitalize()
    summary = (
        f"Expression adjusted using Smart Rewrite v3 (Hugging Face) "
        f"with '{tone_label}' tone and '{style_label}' writing style."
    )

    return {
        "correctedText": rewritten,
        "changesSummary": summary,
    }
