from __future__ import annotations

from typing import Final

import requests
from google import genai
from google.genai import types

from src.config import get_stability_api_url, get_text_model
from src.utils import clean_text


STYLE_PRESETS: Final[dict[str, str]] = {
    "Fantasía": "fantasy-art",
    "Ciencia ficción": "cinematic",
    "Marketing": "photographic",
}


def _build_files_payload() -> dict[str, str]:
    return {"none": ""}


def generate_image(
    generated_text: str,
    style: str,
    api_key: str,
    gemini_api_key: str,
    aspect_ratio: str = "1:1",
    output_format: str = "png",
) -> dict[str, str | bytes]:
    image_prompt = build_image_prompt_english(
        generated_text=generated_text,
        style=style,
        api_key=gemini_api_key,
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }
    form_data = {
        "prompt": image_prompt,
        "negative_prompt": "",
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "seed": "0",
    }
    style_preset = STYLE_PRESETS.get(style)
    if style_preset:
        form_data["style_preset"] = style_preset

    try:
        response = requests.post(
            get_stability_api_url(),
            headers=headers,
            files=_build_files_payload(),
            data=form_data,
            timeout=120,
        )
    except requests.Timeout as exc:
        raise RuntimeError(
            "La solicitud a Stability AI excedió el tiempo de espera. Intenta nuevamente."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(
            "No fue posible conectarse con Stability AI para generar la imagen."
        ) from exc

    if response.ok:
        return {
            "image_bytes": response.content,
            "mime_type": f"image/{output_format}",
            "image_prompt": image_prompt,
        }

    detail = _extract_error_detail(response)
    raise RuntimeError(f"Stability AI devolvió un error al generar la imagen: {detail}")


def build_image_prompt_english(generated_text: str, style: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    style_guidance = {
        "Fantasía": "fantasy art, cinematic lighting, magical atmosphere",
        "Ciencia ficción": "science fiction, futuristic design, dramatic lighting",
        "Marketing": "commercial product photography, premium lighting, clean composition",
    }
    prompt = f"""
You convert Spanish creative text into a short English-only image prompt for Stability AI.

Requirements:
- Output only one prompt in English.
- Keep it between 20 and 60 words.
- Describe visible subjects, setting, mood, lighting, and composition.
- Do not use Spanish words.
- Do not include instructions, bullet points, quotes, or explanations.
- Do not mention text overlays or watermarks.
- Include this visual direction when relevant: {style_guidance.get(style, "cinematic composition")}.

Spanish source text:
{generated_text}
""".strip()

    try:
        response = client.models.generate_content(
            model=get_text_model(),
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            "No fue posible convertir el texto generado a un prompt visual en inglés para Stability AI."
        ) from exc

    result = clean_text(response.text or "")
    if not result:
        raise RuntimeError(
            "Gemini no devolvió un prompt visual utilizable para la generación de imagen."
        )
    return result


def _extract_error_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:300]}"

    if isinstance(payload, dict):
        if "message" in payload:
            return f"HTTP {response.status_code}: {payload['message']}"
        if "name" in payload:
            return f"HTTP {response.status_code}: {payload['name']}"
        if "errors" in payload:
            return f"HTTP {response.status_code}: {payload['errors']}"

    return f"HTTP {response.status_code}: {payload}"
