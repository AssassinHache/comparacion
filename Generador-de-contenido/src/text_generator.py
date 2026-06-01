from __future__ import annotations

from google import genai
from google.genai import types

from src.config import get_text_model
from src.prompts import build_text_prompt
from src.utils import clean_text


def generate_text(
    user_prompt: str,
    content_type: str,
    style: str,
    length: int,
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = build_text_prompt(user_prompt, content_type, style, length)

    try:
        response = client.models.generate_content(
            model=get_text_model(),
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Responde siempre en español. Prioriza creatividad, claridad y coherencia. "
                    "No incluyas explicaciones fuera del texto solicitado."
                ),
                temperature=0.9,
            ),
        )
        result = clean_text(response.text or "")
        if not result:
            raise RuntimeError("El modelo no devolvió texto utilizable.")
        return result
    except Exception as exc:
        message = str(exc)
        raise RuntimeError(
            "Gemini no pudo generar el texto. "
            f"Detalle: {message}"
        ) from exc
