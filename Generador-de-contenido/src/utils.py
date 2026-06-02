from __future__ import annotations

from datetime import datetime
import re


def clean_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def shorten_text(text: str, max_chars: int = 320) -> str:
    text = clean_text(text).replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def extract_visual_essence(generated_text: str) -> str:
    text = clean_text(generated_text).replace("\n", " ")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected = " ".join(sentences[:3]).strip()
    return selected or text


def make_download_name(prefix: str, extension: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def call_gemini_with_retry(func, *args, **kwargs):
    """
    Executes a Gemini API function, automatically retrying with exponential backoff 
    if a 429 Rate Limit (RESOURCE_EXHAUSTED) error is encountered.
    """
    import time
    delay = 2.0
    for attempt in range(4):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            err_msg = str(exc)
            is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
            
            if is_rate_limit and attempt < 3:
                print(f"[Gemini API 429 Rate Limit] Límite superado. Esperando {delay}s antes de reintentar (Intento {attempt+1}/4)...")
                time.sleep(delay)
                delay *= 2.0
                continue
            raise exc

