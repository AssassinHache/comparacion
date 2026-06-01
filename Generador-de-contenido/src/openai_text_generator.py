from __future__ import annotations

import requests
from src.config import get_openai_api_key, get_openai_model
from src.utils import clean_text

def generate_text_openai(
    user_prompt: str,
    content_type: str,
    style: str,
    length: int,
    api_key: str | None = None,
) -> str:
    if not api_key:
        try:
            api_key = get_openai_api_key()
        except ValueError:
            # Fallback mock for demo if no key is provided
            return f"[Simulación GPT-4o] Érase una vez un mundo donde '{user_prompt}' cobraba vida. Esta historia en estilo {style} de tipo {content_type} nos enseña el gran potencial de comparar modelos. GPT-4o resalta la estructura narrativa y el vocabulario refinado en sus {length} palabras de extensión."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    system_instruction = (
        "Responde siempre en español. Prioriza creatividad, claridad y coherencia. "
        "No incluyas explicaciones fuera del texto solicitado. Genera un contenido único basado en las especificaciones del usuario."
    )
    
    prompt = (
        f"Crea un texto del tipo '{content_type}' con el estilo '{style}'. "
        f"La idea o tema base es: '{user_prompt}'. "
        f"El texto debe tener una extensión aproximada de {length} palabras. "
        f"Evita introducciones como 'Aquí tienes tu cuento:' e inicia directamente con el contenido."
    )
    
    payload = {
        "model": get_openai_model(),
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            return clean_text(result)
        else:
            raise RuntimeError(f"OpenAI API retornó código {response.status_code}: {response.text}")
    except Exception as exc:
        # Fallback to simulation if api fails but let user know
        return f"[Simulación GPT-4o - Fallback por Error: {str(exc)}] Érase una vez una maravillosa aventura inspirada en '{user_prompt}'. En el mágico estilo {style}, este relato de tipo {content_type} fluye con gracia intelectual. GPT-4o ofrece una perspectiva rica, descriptiva y emocional."
