from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import language_tool_python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ---------------------------
# FastAPI app + CORS
# ---------------------------
app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # 🔴 your deployed frontend URL (Vercel)
    "https://grammar-correction-ai-by-shahid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # you can use ["*"] while testing if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "TypePolish backend running"}


# ---------------------------
# Grammar tool (LanguageTool)
# ---------------------------
tool = language_tool_python.LanguageTool("en-US")


def apply_language_tool(text: str) -> str:
    """
    Basic grammar + spelling correction using LanguageTool.
    """
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)
    return corrected.strip()


# ---------------------------
# AI paraphrase model (offline T5)
# ---------------------------
PARA_MODEL_NAME = "t5-base"  # small enough + decent quality

# Important: use_fast=False to avoid protobuf issues
para_tokenizer = AutoTokenizer.from_pretrained(PARA_MODEL_NAME, use_fast=False)
para_model = AutoModelForSeq2SeqLM.from_pretrained(PARA_MODEL_NAME)


def smart_rewrite_v3(
    text: str,
    tone: str = "neutral",
    style: str = "neutral",
) -> str:
    """
    Smart Rewrite v3:
    - Uses T5 to paraphrase
    - Adds tone & style instructions
    - Light post-processing (sentence splits etc.)
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
        f"Text: {text}"
    )

    inputs = para_tokenizer(
        instruction,
        return_tensors="pt",
        truncation=True,
        max_length=256,
    )

    outputs = para_model.generate(
        **inputs,
        max_new_tokens=160,
        num_beams=5,
        do_sample=False,
        early_stopping=True,
    )

    raw = para_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # --- Light post-processing: fix spaces and sentence endings ---
    cleaned = " ".join(raw.split())
    # Ensure first char capital
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    # Make sure it ends with punctuation
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."

    return cleaned


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
    """
    cleaned = text.strip()
    if not cleaned:
        return "", "No text provided."

    corrected = apply_language_tool(cleaned)
    corrected = basic_tone_adjust(corrected, mode)

    # Capitalize first letter
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]

    # Ensure punctuation
    if corrected and corrected[-1] not in ".!?":
        corrected += "."

    summary = f"Grammar and spelling corrected using LanguageTool with {mode} style."
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
    2) AI paraphrase with tone + style
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

    rewritten = smart_rewrite_v3(grammared, tone=tone, style=style)

    # Build human-readable summary
    tone_label = tone.capitalize()
    style_label = style.capitalize()
    summary = (
        f"Expression adjusted using Smart Rewrite v3 "
        f"with '{tone_label}' tone and '{style_label}' writing style."
    )

    return {
        "correctedText": rewritten,
        "changesSummary": summary,
    }
