from __future__ import annotations

from google import genai
from google.genai import types
from src.config import get_gemini_api_key

def analyze_image_gemini_2_5(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str | None = None
) -> str:
    """
    Analyzes an uploaded image with a prompt using Google's gemini-2.5-flash (Model A).
    """
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return f"[Simulacion Gemini 2.5 Vision] Analizando imagen de referencia para '{prompt}': Observo una composicion equilibrada con tonos nitidos y un enfoque claro en los elementos principales. Gemini 2.5 destaca la iluminacion y los contrastes."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                ),
                prompt
            ]
        )
        return response.text or "No se pudo extraer texto del analisis."
    except Exception as exc:
        return f"[Simulacion Gemini 2.5 Vision - Fallback por Error: {str(exc)}] Viendo tu imagen y respondiendo a '{prompt}': El modelo percibe un diseño de alta calidad con elementos alineados armónicamente."

def analyze_image_gemini_1_5(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str | None = None
) -> str:
    """
    Analyzes an uploaded image with a prompt using Google's gemini-1.5-flash (Model B).
    Uses the exact same free Gemini API key.
    """
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return f"[Simulacion Gemini 1.5 Vision] Procesando imagen con Gemini 1.5 para '{prompt}': El modelo identifica los elementos estructurales primarios y ofrece una descripcion directa del encuadre y la paleta de colores."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                ),
                prompt
            ]
        )
        return response.text or "No se pudo extraer texto del analisis."
    except Exception as exc:
        return f"[Simulacion Gemini 1.5 Vision - Fallback por Error: {str(exc)}] De acuerdo a tu solicitud '{prompt}': Mi analisis visual detecta contrastes marcados y una excelente profundidad de campo."
