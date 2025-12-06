from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal

import language_tool_python
from language_tool_python.exceptions import RateLimitError

# -------------------------------------------------
# FastAPI app + CORS
# -------------------------------------------------

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://grammar-correction-ai-by-shahid.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # for quick testing you could temporarily use ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# LanguageTool (grammar) – SAFE lazy init
# -------------------------------------------------

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
    except RateLimitError:
        _lt_tool = None
        return None
    except Exception:
        _lt_tool = None
        return None


class TextRequest(BaseModel):
    text: str
    mode: Optional[str] = "grammar"  # "grammar" | "professional" | "casual"


def simple_correct(text: str, mode: str = "grammar"):
    updated = text.strip()
    if not updated:
        return "", "No text provided."

    lt_used = False
    tool = get_language_tool()

    # 1) Grammar + spelling via LanguageTool if available
    if tool is not None:
        try:
            matches = tool.check(updated)
            updated = language_tool_python.utils.correct(updated, matches)
            lt_used = True
        except RateLimitError:
            lt_used = False
        except Exception:
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
            "LanguageToolPublicAPI was not available (rate limit or network error)."
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
# Smart Rewrite v3 – lightweight version (no T5)
# -------------------------------------------------

class AIRewriteRequest(BaseModel):
    text: str
    tone: Literal["friendly", "professional", "confident", "caring", "persuasive"] = "friendly"
    style: Literal["neutral", "student", "corporate", "ielts", "soft"] = "neutral"


def apply_tone_style(text: str, tone: str, style: str) -> str:
    """
    Very lightweight, rule-based "rewrite" so endpoint still works
    on free tier without heavy ML models.
    """

    rewritten = text

    # tiny tone hints (just to differentiate a bit)
    if tone == "friendly":
        rewritten = rewritten.replace("Regards,", "Best regards,")
    elif tone == "professional":
        rewritten = rewritten.replace("thanks", "thank you").replace("Thanks", "Thank you")
    elif tone == "confident":
        if "I think" in rewritten:
            rewritten = rewritten.replace("I think", "I am confident that")
    elif tone == "caring":
        if "sorry" not in rewritten.lower():
            rewritten = "I’m really sorry for any inconvenience. " + rewritten
    elif tone == "persuasive":
        if "please" not in rewritten.lower():
            rewritten = rewritten + " Please consider this request."

    # style hints
    if style == "student":
        rewritten += " This will really help me with my studies."
    elif style == "corporate":
        if not rewritten.endswith(("Regards.", "Regards,")):
            rewritten += " Regards,"
    elif style == "ielts":
        rewritten += " Overall, this reflects my viewpoint in a clear and structured manner."
    elif style == "soft":
        rewritten = "I hope you understand. " + rewritten

    return rewritten.strip()


@app.post("/polish-ai")
def polish_ai(body: AIRewriteRequest):
    # Step 1: basic grammar fix (best-effort)
    base_corrected, _ = simple_correct(body.text, "grammar")

    # Step 2: simple tone/style tweaks (no heavy model)
    polished_text = apply_tone_style(base_corrected, body.tone, body.style)

    summary = (
        f"Expression adjusted using lightweight Smart Rewrite with "
        f"'{body.tone}' tone and '{body.style}' writing style."
    )

    return {
        "correctedText": polished_text,
        "changesSummary": summary,
        "appliedTone": body.tone,
        "appliedStyle": body.style,
    }
