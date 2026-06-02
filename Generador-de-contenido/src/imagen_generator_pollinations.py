from __future__ import annotations

import urllib.parse
import requests
import time

def make_request_with_retries(method: str, url: str, **kwargs) -> requests.Response | None:
    """
    Helper function to perform HTTP requests with automatic retries on 429 rate limit errors.
    """
    for attempt in range(4):
        try:
            if method.lower() == 'post':
                response = requests.post(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)
                
            if response.status_code == 429:
                print(f"[Pollinations Image 429 Rate Limit] Recibido 429 (Intento {attempt+1}/4). Esperando 1.5s...")
                time.sleep(1.5)
                continue
                
            return response
        except Exception as exc:
            if attempt == 3:
                print(f"[Pollinations Image Connection Error] Error en intento final: {exc}")
                break
            time.sleep(1)
    return None

def generate_image_pollinations(
    prompt: str,
    style: str,
    aspect_ratio: str = "1:1",
    seed: int = 42
) -> dict[str, str | bytes]:
    """
    Generates a free image using Pollinations.ai (Flux model) GET endpoint.
    Includes custom User-Agent headers to prevent Cloudflare/WAF block issues and retries on 429 errors.
    """
    # 1. Determine dimensions based on aspect ratio
    dimensions = {
        "1:1": (1024, 1024),
        "16:9": (1024, 576),
        "9:16": (576, 1024),
        "4:3": (1024, 768),
        "3:4": (768, 1024)
    }
    
    width, height = dimensions.get(aspect_ratio, (1024, 1024))
    
    # 2. Build full descriptive prompt including chosen style
    full_prompt = f"{prompt}, high quality, style: {style}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 3. Pollinations GET URL
    url = f"https://image.pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={seed}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = make_request_with_retries("get", url, headers=headers, timeout=40)
        if response and response.ok:
            return {
                "image_bytes": response.content,
                "mime_type": "image/jpeg",
                "image_url": url,
                "is_fallback": False
            }
        else:
            status = response.status_code if response else 'No Response'
            raise RuntimeError(f"Pollinations API retorno codigo {status}")
    except Exception as exc:
        print(f"Error calling Pollinations.ai with original prompt: {exc}. Intentando generación de respaldo...")
        
        # Predefined safe prompts for active generation fallbacks (no static default images)
        SAFE_FALLBACK_PROMPTS = {
            "Fantasía": "A beautiful fantasy landscape with a glowing magical river, majestic mountains, detailed digital art",
            "Ciencia ficción": "A futuristic space station orbiting a beautiful planet, sci-fi cinematic composition",
            "Marketing": "A premium minimalist workspace with a modern laptop, soft studio lighting, clean background",
            "default": "A beautiful tropical sunset over a calm ocean, high quality landscape photography"
        }
        
        fallback_prompt = SAFE_FALLBACK_PROMPTS.get(style, SAFE_FALLBACK_PROMPTS["default"])
        encoded_fallback = urllib.parse.quote(fallback_prompt)
        fallback_url = f"https://image.pollinations.ai/p/{encoded_fallback}?width={width}&height={height}&model=flux&nologo=true&seed=99"
        
        try:
            # Actively call the generation API to create the fallback image on the fly
            response = make_request_with_retries("get", fallback_url, headers=headers, timeout=35)
            if response and response.ok:
                return {
                    "image_bytes": response.content,
                    "mime_type": "image/jpeg",
                    "image_url": fallback_url,
                    "is_fallback": True
                }
        except Exception as inner_exc:
            print(f"Error en generación activa de respaldo de Pollinations: {inner_exc}")
            
        return {
            "image_bytes": b"",
            "mime_type": "image/jpeg",
            "image_url": fallback_url,
            "is_fallback": True
        }
