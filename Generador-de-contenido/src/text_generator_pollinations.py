from __future__ import annotations

import json
import urllib.parse
import requests
import time

def make_request_with_retries(method: str, url: str, **kwargs) -> requests.Response | None:
    """
    Helper function to perform HTTP requests with automatic retries on 429 rate limit errors
    or connection problems.
    """
    for attempt in range(4):
        try:
            if method.lower() == 'post':
                response = requests.post(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)
                
            if response.status_code == 429:
                print(f"[Pollinations 429 Rate Limit] Recibido 429 (Intento {attempt+1}/4). Esperando 1.5s...")
                time.sleep(1.5)
                continue
                
            return response
        except Exception as exc:
            if attempt == 3:
                print(f"[Pollinations Connection Error] Error en intento final: {exc}")
                break
            time.sleep(1)
    return None

def generate_text_pollinations(
    prompt: str,
    content_type: str,
    style: str,
    length: int
) -> str:
    """
    Generates text using Pollinations.ai with multi-layered cascade fallbacks and 429 retry loops.
    """
    system_instruction = (
        f"Actua como un redactor profesional en español. "
        f"Crea un texto de tipo '{content_type}' con el estilo '{style}'. "
        f"El texto debe tener aproximadamente {length} palabras. "
        f"Entrega directamente el texto solicitado sin comentarios extras, saludos, titulos ni explicaciones."
    )
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Layer 1: POST request with 'openai-fast' model
    try:
        payload = {
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "model": "openai-fast",
            "stream": False
        }
        
        response = make_request_with_retries(
            "post",
            "https://text.pollinations.ai/",
            json=payload,
            headers=headers,
            timeout=20
        )
        
        if response and response.ok:
            resp_text = response.text.strip()
            try:
                data = json.loads(resp_text)
                if isinstance(data, dict) and "choices" in data:
                    return data["choices"][0]["message"]["content"].strip()
            except ValueError:
                if resp_text:
                    return resp_text
            if resp_text:
                return resp_text
    except Exception as exc:
        print(f"[Pollinations Layer 1 failed]: {exc}")

    # Layer 2: POST request with 'openai' model
    try:
        payload = {
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "model": "openai",
            "stream": False
        }
        
        response = make_request_with_retries(
            "post",
            "https://text.pollinations.ai/",
            json=payload,
            headers=headers,
            timeout=20
        )
        
        if response and response.ok:
            resp_text = response.text.strip()
            try:
                data = json.loads(resp_text)
                if isinstance(data, dict) and "choices" in data:
                    return data["choices"][0]["message"]["content"].strip()
            except ValueError:
                if resp_text:
                    return resp_text
            if resp_text:
                return resp_text
    except Exception as exc:
        print(f"[Pollinations Layer 2 failed]: {exc}")

    # Layer 3: Legacy GET Request with encoded prompt
    try:
        full_instruction = f"{system_instruction}\n\nInstruccion del usuario: {prompt}"
        encoded_prompt = urllib.parse.quote(full_instruction)
        url = f"https://text.pollinations.ai/{encoded_prompt}"
        
        response = make_request_with_retries(
            "get",
            url,
            headers={"User-Agent": headers["User-Agent"]},
            timeout=20
        )
        if response and response.ok and response.text.strip():
            return response.text.strip()
    except Exception as exc:
        print(f"[Pollinations Layer 3 failed]: {exc}")

    # Final Fallback: Simulated quality offline response
    return (
        f"[Llama 3 - Simulación Offline]: No se pudo establecer conexión estable con los servidores de Pollinations en este momento. "
        f"Aquí tienes un borrador simulado para tu {content_type} en estilo {style}: "
        f"El viento susurraba entre los árboles del bosque mientras avanzaba el camino. Todo parecía quieto y misterioso, "
        f"tal como se describe en la idea principal: '{prompt}'. De pronto, un destello lejano rompió la penumbra, "
        f"señalando el comienzo de una aventura de descubrimiento..."
    )
