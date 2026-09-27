"""
Gemini client for EduGenie.

Kept separate from the Flask routes so the AI logic can be tested or swapped
(for example, for a different model) without touching the web layer.

Uses the current `google-genai` SDK. The older `google-generativeai` package is
deprecated, and the gemini-1.5-* / gemini-2.5-* models are on their way out, so
the default is a current 3.x Flash model.
"""

import os
import time

from google import genai
from google.genai import types

# gemini-3.5-flash is GA with no retirement announced. Swap freely via
# GEMINI_MODEL, or use the gemini-flash-latest alias to always track newest.
DEFAULT_MODEL = "gemini-3.5-flash"

# Instruction prefixes that shape each feature's output.
PROMPTS = {
    "ask": (
        "You are EduGenie, a friendly tutor for college students. "
        "Answer the question clearly and concisely. Use short paragraphs or "
        "bullet points, and keep the tone encouraging. If the question is "
        "ambiguous, state the assumption you made."
    ),
    "summarize": (
        "You are EduGenie, a study assistant. Summarize the student's notes "
        "into exactly 3 short bullet points, then add one line titled "
        "'Key term to revise' naming the single most important concept."
    ),
    "quiz": (
        "You are EduGenie, a quiz generator. Produce exactly 5 multiple-choice "
        "questions on the given topic. Format each question as:\n"
        "Q1. <question>\n"
        "A) <option>\nB) <option>\nC) <option>\nD) <option>\n"
        "Answer: <letter>\n"
        "Never reveal the answer letter before all 5 questions are listed."
    ),
}

MAX_INPUT_CHARS = 8000

# Retry budget for transient Gemini failures (rate limit / 5xx / high demand).
MAX_ATTEMPTS = 4
BACKOFF_BASE = 1.5  # seconds; grows 1.5x, 3x, 6x across attempts

# Module-level client, set by configure() at startup.
_client = None


class GeminiError(RuntimeError):
    """Raised when the Gemini API call cannot be completed."""


def configure():
    """Read config from the environment. Call once at startup."""
    global _client

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Add it to your .env file "
            "(see .env.example)."
        )

    _client = genai.Client(api_key=api_key)
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _call_once(model_name, system_instruction, user_input):
    response = _client.models.generate_content(
        model=model_name,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            # No tools are declared, so skip the automatic function-calling
            # loop the SDK would otherwise set up (and warn about).
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )
    return (response.text or "").strip()


def generate(model_name, feature, user_input):
    """Send one prompt to Gemini and return the text response.

    Retries transient failures (429 / 500 / 503 "high demand") with exponential
    backoff, because the free tier rejects roughly one request in three.
    """
    if _client is None:
        raise GeminiError("Gemini client was not configured.")

    user_input = (user_input or "").strip()
    if not user_input:
        raise GeminiError("Input is empty. Please type something first.")
    if len(user_input) > MAX_INPUT_CHARS:
        raise GeminiError(
            f"Input is too long ({len(user_input)} characters). "
            f"Please keep it under {MAX_INPUT_CHARS}."
        )

    system_instruction = PROMPTS.get(feature, PROMPTS["ask"])
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            text = _call_once(model_name, system_instruction, user_input)
            if not text:
                raise GeminiError(
                    "Gemini returned an empty response. Try rephrasing your input."
                )
            return text
        except GeminiError:
            raise
        except Exception as exc:
            last_error = exc
            if not _is_transient(exc) or attempt == MAX_ATTEMPTS:
                break
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            print(f"Gemini busy ({attempt}/{MAX_ATTEMPTS}), retrying in {wait:.1f}s")
            time.sleep(wait)

    raise GeminiError(_friendly(last_error)) from last_error


def _is_transient(exc):
    """True for errors worth retrying: rate limits, 5xx, and flaky networks."""
    text = str(exc).lower()
    if "safety" in text or "blocked" in text or "recitation" in text:
        return False  # retrying a safety block just wastes quota
    markers = (
        "429", "500", "502", "503", "504",
        "resource_exhausted", "unavailable", "internal",
        "deadline exceeded", "timed out", "timeout",
        "connection", "temporarily", "high demand",
    )
    return any(marker in text for marker in markers)


def _friendly(exc):
    text = str(exc)
    lowered = text.lower()
    if "api_key" in lowered or "api key" in lowered:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
    if "429" in text or "quota" in lowered or "resource_exhausted" in lowered:
        return "Gemini's free quota is used up. Wait a minute and try again."
    if "503" in text or "unavailable" in lowered or "high demand" in lowered:
        return ("Gemini is busy right now (high demand). This is Google's side, "
                "not yours - wait a few seconds and press the button again.")
    if "blocked" in lowered or "safety" in lowered or "recitation" in lowered:
        return "Gemini blocked that request. Try different wording."
    if "not found" in lowered and "model" in lowered:
        model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        return ("Model '" + model + "' is unavailable for this API key. "
                "Try a different GEMINI_MODEL in .env.")
    if "timeout" in lowered or "deadline" in lowered:
        return "Gemini took too long to respond. Try again."
    return f"Gemini request failed: {text}"
