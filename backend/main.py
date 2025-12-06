from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal

import language_tool_python

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# -------------------------------------------------
# FastAPI app + CORS
# -------------------------------------------------

app = FastAPI()

# NOTE:
#  - Don't put trailing "/" in origins
#  - Add your Vercel frontend here
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://grammar-correction-ai-by-shahid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # for quick testing you can use ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# LanguageTool (grammar) - using PUBLIC API
# -------------------------------------------------

# This version does NOT require Java. It calls LanguageTool's public HTTP API.
tool = language_tool_python.LanguageToolPublicAPI("en-US")


class TextRequest(BaseModel):
    text: str
    mode: Optional[str] = "grammar"  # "grammar" | "professional" | "casual"


def simple_correct(text: str, mode: str = "grammar"):
    updated = text.strip()
    if not updated:
        return "", "No text provided."

    # 1) Grammar + spelling via LanguageTool
    try:
        matches = tool.check(updated)
        updated = language_tool_python.utils.correct(updated, matches)
        lt_used = True
    except Exception:
        # If LanguageTool public API fails, don't crash the whole backend
        lt_used = False

    # 2) Capitalize first letter
    updated = updated.strip()
    if updated:
        updated = updated[0].upper() + updated[1:]

    # 3) Ensure punctuation
    if updated and updated[-1] not in ".!?":
        updated += "."

    # 4) Tone tweaks
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

    if lt_used:
        summary = f"Grammar and spelling corrected using LanguageTool with {mode} style."
    else:
        summary = (
            f"Basic cleanup applied with {mode} style. "
            "LanguageToolPublicAPI was not available at the moment."
        )

    return updated, summary


@app.get("/")
def read_root():
    return {"message": "TypePolish backend running"}


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


# -------------------------------------------------
# Smart Rewrite v3 – offline T5 paraphraser
# -------------------------------------------------

# NOTE:
# flan-t5-large is heavy and may crash on small Render instances.
# You can try flan-t5-base which uses less memory.
PARA_MODEL_NAME = "google/flan-t5-base"  # change back to flan-t5-large if your instance can handle it

para_tokenizer = AutoTokenizer.from_pretrained(PARA_MODEL_NAME)
para_model = AutoModelForSeq2SeqLM.from_pretrained(PARA_MODEL_NAME)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
para_model.to(DEVICE)


class AIRewriteRequest(BaseModel):
    text: str
    tone: Literal["friendly", "professional", "confident", "caring", "persuasive"] = "friendly"
    style: Literal["neutral", "student", "corporate", "ielts", "soft"] = "neutral"


def build_ai_prompt(text: str, tone: str, style: str) -> str:
    tone_part = {
        "friendly": "Make it sound warm, friendly and supportive.",
        "professional": "Make it sound clear, polite and professional.",
        "confident": "Make it sound confident and positive.",
        "caring": "Make it sound kind, empathetic and caring.",
        "persuasive": "Make it more convincing and persuasive.",
    }.get(tone, "Use a natural tone.")

    style_part = {
        "neutral": "Use simple, natural English.",
        "student": "Use easy, student-friendly English.",
        "corporate": "Use a formal office / corporate writing style.",
        "ielts": "Use clear, well-structured English suitable for IELTS writing.",
        "soft": "Use a soft, gentle and understanding style.",
    }.get(style, "Use simple, natural English.")

    prompt = (
        "Rewrite the following text in fluent English.\n"
        f"{tone_part}\n"
        f"{style_part}\n"
        "Keep the meaning the same. Do not add explanations.\n\n"
        f"Text: {text}\n\n"
        "Rewritten:"
    )
    return prompt


def cleanup_generated(text: str) -> str:
    text = text.strip()
    if text.lower().startswith("rewritten:"):
        text = text[len("rewritten:") :].strip()
    return text


@app.post("/polish-ai")
def polish_ai(body: AIRewriteRequest):
    # Step 1: basic grammar fix
    base_corrected, _ = simple_correct(body.text, "grammar")

    # Step 2: build prompt
    prompt = build_ai_prompt(base_corrected, body.tone, body.style)

    # Step 3: run T5 model
    inputs = para_tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    ).to(DEVICE)

    with torch.no_grad():
        outputs = para_model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    rewritten = para_tokenizer.decode(outputs[0], skip_special_tokens=True)
    polished_text = cleanup_generated(rewritten)

    summary = (
        f"Expression adjusted using Smart Rewrite v3 with "
        f"'{body.tone}' tone and '{body.style}' writing style."
    )

    # frontend expects correctedText
    return {
        "correctedText": polished_text,
        "changesSummary": summary,
        "appliedTone": body.tone,
        "appliedStyle": body.style,
    }
