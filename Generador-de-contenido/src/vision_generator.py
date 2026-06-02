from __future__ import annotations

import base64
import requests
from google import genai
from google.genai import types
from src.config import get_gemini_api_key, get_openai_api_key, get_groq_api_key, get_groq_vision_model
from src.utils import call_gemini_with_retry

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
        
        def run_call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    ),
                    prompt
                ]
            )
            
        response = call_gemini_with_retry(run_call)
        return response.text or "No se pudo extraer texto del analisis."
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "[Error de Límite de Cuota - Gemini 2.5]: Has superado el límite de peticiones de tu clave API. Por favor, espera unos segundos e inténtalo de nuevo."
        elif "403" in error_msg or "API_KEY_INVALID" in error_msg:
            return "[Error de Autenticación - Gemini 2.5]: Clave de API inválida o sin permisos. Revisa tu archivo .env."
        else:
            return f"[Error de Procesamiento - Gemini 2.5]: {error_msg}"

def analyze_image_gemini_2_0(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str | None = None
) -> str:
    """
    Analyzes an uploaded image with a prompt using Google's gemini-2.0-flash (Model B).
    Uses the exact same free Gemini API key.
    """
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return f"[Simulacion Gemini 2.0 Vision] Procesando imagen con Gemini 2.0 para '{prompt}': El modelo identifica los elementos estructurales primarios y ofrece una descripcion directa del encuadre y la paleta de colores."

    try:
        client = genai.Client(api_key=api_key)
        
        def run_call():
            return client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    ),
                    prompt
                ]
            )
            
        response = call_gemini_with_retry(run_call)
        return response.text or "No se pudo extraer texto del analisis."
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "[Error de Límite de Cuota - Gemini 2.0]: Has superado el límite de peticiones de tu clave API. Por favor, espera unos segundos e inténtalo de nuevo."
        elif "403" in error_msg or "API_KEY_INVALID" in error_msg:
            return "[Error de Autenticación - Gemini 2.0]: Clave de API inválida o sin permisos. Revisa tu archivo .env."
        else:
            return f"[Error de Procesamiento - Gemini 2.0]: {error_msg}"

def analyze_image_openai(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str | None = None
) -> str:
    """
    Analyzes an uploaded image with a prompt using OpenAI's GPT-4o (Model B).
    """
    if not api_key:
        try:
            api_key = get_openai_api_key()
        except ValueError:
            return f"[Simulacion GPT-4o Vision] Procesando imagen con GPT-4o para '{prompt}': El modelo identifica los elementos estructurales primarios y ofrece una descripcion directa del encuadre y la paleta de colores."

    if not api_key:
        return f"[Simulacion GPT-4o Vision - Sin Key] Analizando imagen de referencia para '{prompt}' en estilo GPT-4o: Observo una composicion equilibrada con tonos nitidos y un enfoque claro en los elementos principales."

    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=40
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise RuntimeError(f"OpenAI Vision API retorno codigo {response.status_code}: {response.text}")
            
    except Exception as exc:
        error_msg = str(exc)
        return f"[Error de Procesamiento - GPT-4o Vision]: {error_msg}"

def analyze_image_groq(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str | None = None
) -> str:
    """
    Analyzes an uploaded image with a prompt using Groq's Llama 3.2 Vision model (Model B).
    """
    if not api_key:
        try:
            api_key = get_groq_api_key()
        except ValueError:
            return f"[Simulacion Groq Llama Vision] Procesando imagen con Groq Llama para '{prompt}': El modelo identifica los elementos estructurales primarios y ofrece una descripcion directa del encuadre y la paleta de colores."

    if not api_key:
        return f"[Simulacion Groq Llama Vision - Sin Key] Analizando imagen de referencia para '{prompt}' en estilo Groq Llama: Observo una composicion equilibrada con tonos nitidos."

    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": get_groq_vision_model(),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=40
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise RuntimeError(f"Groq Vision API retorno codigo {response.status_code}: {response.text}")
            
    except Exception as exc:
        error_msg = str(exc)
        return f"[Error de Procesamiento - Groq Llama Vision]: {error_msg}"
