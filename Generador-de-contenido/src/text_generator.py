from __future__ import annotations

from google import genai
from google.genai import types

from src.config import get_text_model
from src.prompts import build_text_prompt
from src.utils import clean_text, call_gemini_with_retry

def generate_text(
    user_prompt: str,
    content_type: str,
    style: str,
    length: int,
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)

    try:
        def run_call():
            return client.models.generate_content(
                model=get_text_model(),
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Responde siempre en español. Responde de forma directa, útil, precisa y totalmente libre. "
                        "No impongas formatos de cuento o poema a menos que el usuario lo pida."
                    ),
                    temperature=0.7,
                ),
            )
            
        response = call_gemini_with_retry(run_call)
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
