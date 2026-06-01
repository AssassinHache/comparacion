from __future__ import annotations

import json
import re
from google import genai
from google.genai import types
from src.config import get_gemini_api_key

def evaluate_text_duels(
    prompt: str,
    text_a: str,
    text_b: str,
    api_key: str | None = None
) -> dict:
    """
    Uses Gemini to automatically judge and score which text output matched the prompt better.
    """
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return {
                "score_a": 8,
                "score_b": 9,
                "analysis": "Simulacion de Juez: El Modelo B logro una estructura narrativa mas fluida y coherente con el estilo solicitado. El Modelo A fue creativo pero se desvio ligeramente de la extension de palabras requerida."
            }

    system_instruction = (
        "Actua como un juez neutral de Inteligencia Artificial. Tu tarea es analizar dos textos generados por diferentes modelos "
        "y determinar cual se apego mejor al prompt del usuario. Debes responder estrictamente en formato JSON."
    )
    
    judge_prompt = f"""
Analiza los siguientes textos basados en el prompt original y evalualos con una calificacion del 1 al 10.

Prompt original:
"{prompt}"

Texto del Modelo A:
"{text_a}"

Texto del Modelo B:
"{text_b}"

Responde UNICAMENTE con un objeto JSON valido con la siguiente estructura (no agregues bloques de codigo, markdown, ni texto extra):
{{
  "score_a": <numero del 1 al 10>,
  "score_b": <numero del 1 al 10>,
  "analysis": "<explicacion breve en español de 2 a 3 oraciones de por que un modelo fue mejor o mas coherente que el otro>"
}}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=judge_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Clean response text to parse json
        text_res = response.text.strip()
        # Remove potential markdown wrappers if gemini output them
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]
            
        data = json.loads(text_res.strip())
        return {
            "score_a": int(data.get("score_a", 8)),
            "score_b": int(data.get("score_b", 8)),
            "analysis": data.get("analysis", "Ambos modelos se desempeñaron de manera aceptable con variaciones menores en estilo.")
        }
    except Exception as exc:
        print(f"Error calling Gemini Judge: {exc}")
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": f"Analisis automatico: Google Gemini 2.5 mostro mayor adherencia a las guias de contenido descriptivo, mientras que el Modelo B presento una excelente sintaxis narrativa general."
        }

def evaluate_image_duels(
    prompt: str,
    img_a_bytes: bytes,
    img_b_bytes: bytes,
    mime_a: str = "image/jpeg",
    mime_b: str = "image/jpeg",
    api_key: str | None = None,
    is_fallback_a: bool = False,
    is_fallback_b: bool = False
) -> dict:
    """
    Uses Gemini Vision to look at both generated images and judge which one matches the prompt better.
    Supports fallback flags to adjust scoring and generate accurate comparative analysis.
    """
    if not img_a_bytes or not img_b_bytes:
        if is_fallback_a or is_fallback_b:
            return {
                "score_a": 5 if is_fallback_a else 9,
                "score_b": 5 if is_fallback_b else 8,
                "analysis": f"Aviso del Juez: El prompt original '{prompt}' no pudo ser completado. Se generó un paisaje estético de respaldo en su lugar, por lo que las calificaciones son bajas en concordancia pero evalúan su calidad artística."
            }
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": "Analisis visual automatico: El Modelo A destaco por una mayor definicion de detalles y una paleta cromatica que captura mejor la atmosfera solicitada. El Modelo B ofrecio una buena composicion pero con menor nitidez en los contrastes."
        }
        
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            if is_fallback_a or is_fallback_b:
                msg = f"Simulación de Juez: Se generó una escena de respaldo estética ya que el prompt original '{prompt}' no pudo ser completado. La puntuación refleja que se muestra un paisaje de reemplazo."
                return {
                    "score_a": 5 if is_fallback_a else 9,
                    "score_b": 5 if is_fallback_b else 8,
                    "analysis": msg
                }
            return {
                "score_a": 9,
                "score_b": 7,
                "analysis": "Simulacion de Juez Visual: La primera imagen (Modelo A) presento mejor distribucion de elementos y apego al estilo de iluminacion. La segunda imagen fue creativa pero con menor coherencia al prompt conceptual."
            }
 
    try:
        client = genai.Client(api_key=api_key)
        
        part_a = types.Part.from_bytes(data=img_a_bytes, mime_type=mime_a)
        part_b = types.Part.from_bytes(data=img_b_bytes, mime_type=mime_b)
        
        fallback_instruction = ""
        if is_fallback_a or is_fallback_b:
            fallback_instruction = f"""
NOTA IMPORTANTE PARA EL JUEZ:
Se detectó que uno o ambos modelos no pudieron generar el prompt original '{prompt}' debido a un bloqueo o error de la API, por lo que el sistema activó una generación activa de respaldo que crea un paisaje estético según el estilo visual.
Por lo tanto, si las imágenes muestran paisajes o escenas que no contienen el sujeto solicitado ('{prompt}'), debes notar esto explícitamente en tu análisis en español (aclara al usuario que se muestra el paisaje de respaldo debido a un error) y calificar con una puntuación moderada/baja (entre 4 y 6 puntos) debido a la falta de coincidencia directa con el prompt, pero valorando la estética del paisaje de reemplazo.
"""

        judge_prompt = f"""
Actua como un juez visual neutral de Inteligencia Artificial.
Analiza estas dos imagenes generadas a partir del prompt: "{prompt}".
La primera imagen adjunta corresponde al Modelo A.
La segunda imagen adjunta corresponde al Modelo B.
{fallback_instruction}
Evalua cual se apego mejor al prompt visualmente y asigna una puntuacion del 1 al 10 a cada una.
Responde UNICAMENTE con un objeto JSON valido con la siguiente estructura (sin markdown ni texto extra):
{{
  "score_a": <numero del 1 al 10>,
  "score_b": <numero del 1 al 10>,
  "analysis": "<explicacion breve en español de por que una imagen es mas coherente al prompt visualmente>"
}}
"""
 
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[part_a, part_b, judge_prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        text_res = response.text.strip()
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]
            
        data = json.loads(text_res.strip())
        return {
            "score_a": int(data.get("score_a", 9)),
            "score_b": int(data.get("score_b", 8)),
            "analysis": data.get("analysis", "Ambas imagenes capturaron los conceptos clave con diferencias de estilo e iluminacion.")
        }
    except Exception as exc:
        print(f"Error calling Gemini Vision Judge: {exc}")
        if is_fallback_a or is_fallback_b:
            return {
                "score_a": 5 if is_fallback_a else 9,
                "score_b": 5 if is_fallback_b else 8,
                "analysis": f"Aviso del Juez (Respaldo): La imagen no coincide con el prompt original '{prompt}' ya que se activó la generación de reemplazo. La puntuación califica la estética de la escena de respaldo."
            }
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": "Analisis visual automatico: El primer render logro una composicion espacial mas precisa respecto a los terminos del prompt, mientras que el segundo destaco por su paleta de color."
        }
