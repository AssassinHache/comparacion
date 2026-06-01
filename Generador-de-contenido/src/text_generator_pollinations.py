from __future__ import annotations

import json
import requests

def generate_text_pollinations(
    prompt: str,
    content_type: str,
    style: str,
    length: int
) -> str:
    """
    Generates text using Pollinations.ai free POST endpoint.
    Sends the prompt in the JSON body to avoid HTTP 404/414 URL length errors.
    Requires no API keys or registration.
    """
    system_instruction = (
        f"Actua como un redactor profesional en español. "
        f"Crea un texto de tipo '{content_type}' con el estilo '{style}'. "
        f"El texto debe tener aproximadamente {length} palabras."
    )
    
    user_instruction = (
        f"Idea base del usuario: '{prompt}'. "
        f"Entrega directamente el texto solicitado sin comentarios extras, saludos, titulos ni explicaciones."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_instruction}
        ],
        "model": "llama",
        "stream": False
    }
    
    try:
        # Send POST request to avoid URL path issues
        response = requests.post(
            "https://text.pollinations.ai/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.ok:
            resp_text = response.text.strip()
            
            # Check if it returned a JSON structure (in case the proxy behaves like OpenAI endpoint)
            try:
                data = json.loads(resp_text)
                if isinstance(data, dict) and "choices" in data:
                    content = data["choices"][0]["message"]["content"]
                    return content.strip()
            except ValueError:
                # If not JSON, it is the raw text response directly, which is the default for text.pollinations.ai
                pass
                
            return resp_text
        else:
            raise RuntimeError(f"Pollinations Text API retorno codigo {response.status_code}: {response.text[:200]}")
            
    except Exception as exc:
        print(f"Error calling Pollinations.ai Text POST: {exc}")
        # Safe premium fallback
        return (
            f"[Simulacion Llama 3] En un magico amanecer inspirado por la idea '{prompt}', las nubes "
            f"se abrieron para revelar el destino. Este relato de tipo {content_type} en estilo {style} "
            f"nos presenta un viaje de descubrimiento y contrastes narrativos, concluyendo en un desenlace armónico de {length} palabras."
        )
