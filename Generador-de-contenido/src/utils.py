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
