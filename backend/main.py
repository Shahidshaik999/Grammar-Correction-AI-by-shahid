from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import re

import language_tool_python

app = FastAPI()

# ---------- CORS ----------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
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


# ---------- Request Models ----------

class TextRequest(BaseModel):
    text: str
    mode: Optional[str] = "grammar"  # "grammar" | "professional" | "casual"


class AIRequest(BaseModel):
    text: str


class ToneRequest(BaseModel):
    text: str
    tone: str  # "friendly" | "professional" | "confident" | "calm" | "caring" | "persuasive"


# ---------- Helpers ----------

def normalize_spaces(text: str) -> str:
    return " ".join(text.split())


def split_sentences(text: str):
    """
    Split text into sentences, keeping punctuation.
    Very simple splitter, but enough for our use-case.
    """
    parts = re.split(r"([.!?])", text)
    sentences = []
    current = ""

    for part in parts:
        if not part:
            continue
        if part in ".!?":
            current += part
            sentences.append(current.strip())
            current = ""
        else:
            current += part

    if current.strip():
        sentences.append(current.strip())

    return sentences


def smart_rewrite_sentence(sentence: str) -> str:
    """
    Smart Rewrite v2:
    - Softly improve flow
    - Remove weak phrases
    - Improve connectors
    - Make subject-pronoun usage more natural
    """

    s = sentence.strip()

    # Basic: ensure single spaces
    s = normalize_spaces(s)

    # Fix lowercase "i" to "I"
    s = re.sub(r"\bi\b", "I", s)

    # 1) Weak phrase cleanup
    weak_map = {
        "I think that ": "",
        "I think ": "",
        "maybe ": "",
        "probably ": "",
        "kind of ": "",
        "sort of ": "",
        "a little bit ": "a bit ",
    }
    for k, v in weak_map.items():
        s = s.replace(k, v)

    # 2) Tense / phrasing smoothing
    replacements = {
        "I want to tell him that": "I wanted to let him know that",
        "I want to tell her that": "I wanted to let her know that",
        "I want to tell them that": "I wanted to let them know that",
        "I want to tell you that": "I wanted to let you know that",
        "I want to tell that": "I wanted to explain that",
        "I want to explain him": "I wanted to explain to him",
        "I want to explain her": "I wanted to explain to her",
        "I want to explain them": "I wanted to explain to them",
        "I will try to": "I will",
        "I will try": "I will",
        "very very": "very",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # 3) Start-of-sentence connectors
    s_strip_lower = s.lower().lstrip()

    if s_strip_lower.startswith("but "):
        # "But later I..." -> "However, later I..."
        s = re.sub(r"^but\s+", "However, ", s, flags=re.IGNORECASE)
    elif s_strip_lower.startswith("and "):
        s = re.sub(r"^and\s+", "", s, flags=re.IGNORECASE)
    elif s_strip_lower.startswith("so "):
        s = re.sub(r"^so\s+", "As a result, ", s, flags=re.IGNORECASE)
    elif s_strip_lower.startswith("then "):
        s = re.sub(r"^then\s+", "Then, ", s, flags=re.IGNORECASE)
    elif s_strip_lower.startswith("later "):
        # "later I realized" -> "Later, I realised"
        s = re.sub(r"^later\s+", "Later, ", s, flags=re.IGNORECASE)

    return s


def smart_rewrite(text: str) -> str:
    """
    Smart Rewrite v2 over the whole paragraph.
    1) Split into sentences
    2) Improve each sentence
    3) Join them back with nice spacing
    """
    text = normalize_spaces(text)
    sentences = split_sentences(text)

    improved = []
    last = ""

    for sent in sentences:
        new_s = smart_rewrite_sentence(sent)

        # Avoid exact duplicates back-to-back
        if new_s == last:
            continue

        improved.append(new_s)
        last = new_s

    return " ".join(improved)


# ---------- Core Grammar Correction ----------

def simple_correct(text: str, mode: str = "grammar"):
    updated = text.strip()
    if not updated:
        return "", "No text provided."

    # 1) Grammar + spelling correction using LanguageTool
    matches = tool.check(updated)
    updated = language_tool_python.utils.correct(updated, matches)

    # 2) Capitalize first letter of the whole text
    updated = updated.strip()
    if updated:
        updated = updated[0].upper() + updated[1:]

    # 3) Ensure ending punctuation
    if updated and updated[-1] not in ".!?":
        updated += "."

    # 4) Simple tone changes (light rules)
    if mode == "professional":
        pro_replacements = {
            " bro": "",
            " gonna": " going to",
            " wanna": " want to",
            " pls": " please",
            " don't": " do not",
            " can't": " cannot",
            " ok ": " okay ",
        }
        for wrong, right in pro_replacements.items():
            updated = updated.replace(wrong, right)

    elif mode == "casual":
        updated = updated.replace(" sir", " bro")

    summary = f"Grammar and spelling corrected using LanguageTool with {mode} style."
    return updated, summary


# ---------- Tone Rewriter (rule-based) ----------

def apply_tone(text: str, tone: str) -> str:
    t = tone.lower()
    result = normalize_spaces(text)

    if t == "friendly":
        result = result.replace("Regards,", "Cheers,")
        result = result.replace("regards,", "cheers,")
        if not result.lower().startswith(("hi", "hello", "hey")):
            result = "Hi, " + result
    elif t == "professional":
        replacements = {
            " bro": "",
            " dude": "",
            " guys": " everyone",
            "yeah": "yes",
            " ok": " okay",
            " ok.": " okay.",
            " okay bro": " okay",
        }
        for wrong, right in replacements.items():
            result = result.replace(wrong, right)
    elif t == "confident":
        weak_phrases = [
            "I think ",
            "maybe ",
            "probably ",
            "I am not sure but ",
        ]
        for w in weak_phrases:
            result = result.replace(w, "")
        result = result.replace("I will try to", "I will")
        result = result.replace("I will try", "I will")
    elif t == "calm":
        strong_to_calm = {
            "I am tired of": "I am concerned about",
            "I am very angry": "I am quite upset",
            "this is unacceptable": "this is not ideal",
            "you never": "you rarely",
            "you always": "you often",
        }
        for k, v in strong_to_calm.items():
            result = result.replace(k, v)
    elif t == "caring":
        if not result.lower().startswith(("i understand", "I understand")):
            result = "I understand how you feel. " + result
        if "sorry" not in result.lower():
            result += " I am here for you and I truly care."
    elif t == "persuasive":
        if "because" not in result.lower():
            result += " This will really help us move forward because it makes things clearer."
    return result


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


# ---------- /polish-ai (Smart Rewrite v2) ----------

@app.post("/polish-ai")
def polish_ai(body: AIRequest):
    base = body.text.strip()
    if not base:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    # Step 1: fix grammar + spelling
    corrected, _ = simple_correct(base, "grammar")

    # Step 2: Smart Rewrite v2 to improve fluency
    fluent = smart_rewrite(corrected)

    return {
        "correctedText": fluent,
        "changesSummary": "Grammar corrected and refined with Smart Rewrite v2 for more natural English.",
    }


# ---------- /rewrite-tone (uses Smart Rewrite too) ----------

@app.post("/rewrite-tone")
def rewrite_tone(body: ToneRequest):
    base = body.text.strip()
    if not base:
        return {
            "correctedText": "",
            "changesSummary": "No text provided.",
        }

    # First, make it fluent
    fluent = smart_rewrite(base)
    # Then apply tone
    toned_text = apply_tone(fluent, body.tone)

    return {
        "correctedText": toned_text,
        "changesSummary": f"Expression adjusted towards '{body.tone}' tone using Smart Rewrite v2.",
    }
