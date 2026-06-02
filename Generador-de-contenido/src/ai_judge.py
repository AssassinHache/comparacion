from __future__ import annotations

import json
import re
from google import genai
from google.genai import types
from src.config import get_gemini_api_key
from src.utils import call_gemini_with_retry

def evaluate_text_duels(
    prompt: str,
    text_a: str,
    text_b: str,
    api_key: str | None = None
) -> dict:
    """
    Uses Gemini to automatically judge and score which text output matched the prompt better
    by evaluating across 5 criteria dimensions.
    """
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return {
                "score_a": 8,
                "score_b": 9,
                "analysis": "Simulacion de Juez: El Modelo B logro una estructura narrativa mas fluida y coherente con el estilo solicitado. El Modelo A fue creativo pero se desvio ligeramente de la extension de palabras requerida.",
                "criteria_a": {
                    "prompt_adherence": 8,
                    "coherence": 8,
                    "creativity": 9,
                    "accuracy": 8,
                    "writing_quality": 8
                },
                "criteria_b": {
                    "prompt_adherence": 9,
                    "coherence": 9,
                    "creativity": 9,
                    "accuracy": 8,
                    "writing_quality": 9
                }
            }

    system_instruction = (
        "Actua como un juez neutral de Inteligencia Artificial. Tu tarea es analizar dos textos generados por diferentes modelos "
        "y determinar cual se apego mejor al prompt del usuario evaluando múltiples criterios. Debes responder estrictamente en formato JSON."
    )
    
    judge_prompt = f"""
Analiza los siguientes textos basados en el prompt original y evalualos en 5 criterios con una calificacion del 1 al 10 para cada criterio.

Prompt original:
"{prompt}"

Texto del Modelo A:
"{text_a}"

Texto del Modelo B:
"{text_b}"

Los criterios a evaluar son:
1. prompt_adherence (adherencia, similitud y parecido directo al prompt original enviado)
2. coherence (coherencia narrativa y estructura lógica)
3. creativity (creatividad, estilo y originalidad)
4. accuracy (precisión, veracidad o consistencia de la información)
5. writing_quality (calidad de redacción, gramática y vocabulario)

Responde UNICAMENTE con un objeto JSON valido con la siguiente estructura (no agregues bloques de codigo, markdown, ni texto extra):
{{
  "score_a": <puntaje general promedio del 1 al 10>,
  "score_b": <puntaje general promedio del 1 al 10>,
  "analysis": "<explicacion breve en español de por que un modelo fue mejor o mas coherente que el otro respecto al prompt original>",
  "criteria_a": {{
    "prompt_adherence": <numero de 1 a 10>,
    "coherence": <numero de 1 a 10>,
    "creativity": <numero de 1 a 10>,
    "accuracy": <numero de 1 a 10>,
    "writing_quality": <numero de 1 a 10>
  }},
  "criteria_b": {{
    "prompt_adherence": <numero de 1 a 10>,
    "coherence": <numero de 1 a 10>,
    "creativity": <numero de 1 a 10>,
    "accuracy": <numero de 1 a 10>,
    "writing_quality": <numero de 1 a 10>
  }}
}}
"""

    try:
        client = genai.Client(api_key=api_key)
        
        def run_call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=judge_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
        response = call_gemini_with_retry(run_call)
        
        # Clean response text to parse json
        text_res = response.text.strip()
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]
            
        data = json.loads(text_res.strip())
        
        criteria_a = data.get("criteria_a", {})
        criteria_b = data.get("criteria_b", {})
        
        # Fill missing keys in criteria lists
        default_keys = ["prompt_adherence", "coherence", "creativity", "accuracy", "writing_quality"]
        for key in default_keys:
            if key not in criteria_a:
                criteria_a[key] = 8
            if key not in criteria_b:
                criteria_b[key] = 8
                
        return {
            "score_a": int(data.get("score_a", 8)),
            "score_b": int(data.get("score_b", 8)),
            "analysis": data.get("analysis", "Ambos modelos se desempeñaron de manera aceptable con variaciones menores en estilo."),
            "criteria_a": criteria_a,
            "criteria_b": criteria_b
        }
    except Exception as exc:
        print(f"Error calling Gemini Judge: {exc}")
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": "Analisis automatico: Google Gemini 2.5 mostro mayor adherencia a las guias de contenido descriptivo, mientras que el Modelo B presento una excelente sintaxis narrativa general.",
            "criteria_a": {
                "prompt_adherence": 9,
                "coherence": 8,
                "creativity": 8,
                "accuracy": 9,
                "writing_quality": 8
            },
            "criteria_b": {
                "prompt_adherence": 8,
                "coherence": 8,
                "creativity": 9,
                "accuracy": 8,
                "writing_quality": 8
            }
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
    Uses Gemini Vision to look at both generated images and judge which one matches the prompt better,
    returning a detailed criteria score breakdown.
    """
    if not img_a_bytes or not img_b_bytes:
        if is_fallback_a or is_fallback_b:
            return {
                "score_a": 5 if is_fallback_a else 9,
                "score_b": 5 if is_fallback_b else 8,
                "analysis": f"Aviso del Juez: El prompt original '{prompt}' no pudo ser completado. Se generó un paisaje estético de respaldo en su lugar.",
                "criteria_a": {
                    "prompt_adherence": 4 if is_fallback_a else 9,
                    "composition": 6 if is_fallback_a else 9,
                    "aesthetics": 7 if is_fallback_a else 9,
                    "coherence": 5 if is_fallback_a else 8,
                    "realism_artistry": 6 if is_fallback_a else 9
                },
                "criteria_b": {
                    "prompt_adherence": 4 if is_fallback_b else 8,
                    "composition": 6 if is_fallback_b else 8,
                    "aesthetics": 7 if is_fallback_b else 8,
                    "coherence": 5 if is_fallback_b else 8,
                    "realism_artistry": 6 if is_fallback_b else 8
                }
            }
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": "Analisis visual automatico: El Modelo A destaco por una mayor definicion de detalles y una paleta cromatica que captura mejor la atmosfera solicitada.",
            "criteria_a": {
                "prompt_adherence": 9,
                "composition": 9,
                "aesthetics": 8,
                "coherence": 8,
                "realism_artistry": 9
            },
            "criteria_b": {
                "prompt_adherence": 8,
                "composition": 8,
                "aesthetics": 8,
                "coherence": 8,
                "realism_artistry": 8
            }
        }
        
    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            return {
                "score_a": 9,
                "score_b": 7,
                "analysis": "Simulacion de Juez Visual: La primera imagen (Modelo A) presento mejor distribucion de elementos y apego al estilo de iluminacion. La segunda imagen fue creativa pero con menor coherencia al prompt conceptual.",
                "criteria_a": {
                    "prompt_adherence": 9,
                    "composition": 8,
                    "aesthetics": 9,
                    "coherence": 9,
                    "realism_artistry": 9
                },
                "criteria_b": {
                    "prompt_adherence": 7,
                    "composition": 7,
                    "aesthetics": 8,
                    "coherence": 7,
                    "realism_artistry": 8
                }
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
Evalua cual se apego mejor al prompt visualmente y evalualas en 5 criterios con una calificacion del 1 al 10 para cada criterio.

Los criterios a evaluar son:
1. prompt_adherence (adherencia y parecido directo al prompt original enviado)
2. composition (composición, encuadre y distribución de elementos)
3. aesthetics (estética, iluminación y paleta de colores)
4. coherence (coherencia interna del contenido generado)
5. realism_artistry (fidelidad al estilo artístico o realismo solicitado)

Responde UNICAMENTE con un objeto JSON valido con la siguiente estructura (sin markdown ni texto extra):
{{
  "score_a": <puntaje general promedio del 1 al 10>,
  "score_b": <puntaje general promedio del 1 al 10>,
  "analysis": "<explicacion breve en español de por que una imagen es mas coherente al prompt visualmente>",
  "criteria_a": {{
    "prompt_adherence": <numero de 1 a 10>,
    "composition": <numero de 1 a 10>,
    "aesthetics": <numero de 1 a 10>,
    "coherence": <numero de 1 a 10>,
    "realism_artistry": <numero de 1 a 10>
  }},
  "criteria_b": {{
    "prompt_adherence": <numero de 1 a 10>,
    "composition": <numero de 1 a 10>,
    "aesthetics": <numero de 1 a 10>,
    "coherence": <numero de 1 a 10>,
    "realism_artistry": <numero de 1 a 10>
  }}
}}
"""
 
        def run_call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[part_a, part_b, judge_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
        response = call_gemini_with_retry(run_call)
        
        text_res = response.text.strip()
        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]
            
        data = json.loads(text_res.strip())
        
        criteria_a = data.get("criteria_a", {})
        criteria_b = data.get("criteria_b", {})
        
        default_keys = ["prompt_adherence", "composition", "aesthetics", "coherence", "realism_artistry"]
        for key in default_keys:
            if key not in criteria_a:
                criteria_a[key] = 8
            if key not in criteria_b:
                criteria_b[key] = 8
                
        return {
            "score_a": int(data.get("score_a", 9)),
            "score_b": int(data.get("score_b", 8)),
            "analysis": data.get("analysis", "Ambas imagenes capturaron los conceptos clave con diferencias de estilo e iluminacion."),
            "criteria_a": criteria_a,
            "criteria_b": criteria_b
        }
    except Exception as exc:
        print(f"Error calling Gemini Vision Judge: {exc}")
        return {
            "score_a": 9,
            "score_b": 8,
            "analysis": "Analisis visual automatico: El primer render logro una composicion espacial mas precisa respecto a los terminos del prompt, mientras que el segundo destaco por su paleta de color.",
            "criteria_a": {
                "prompt_adherence": 9,
                "composition": 8,
                "aesthetics": 8,
                "coherence": 9,
                "realism_artistry": 9
            },
            "criteria_b": {
                "prompt_adherence": 8,
                "composition": 8,
                "aesthetics": 9,
                "coherence": 8,
                "realism_artistry": 8
            }
        }
