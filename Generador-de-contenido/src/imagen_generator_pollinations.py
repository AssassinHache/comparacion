from __future__ import annotations

import urllib.parse
import requests

def generate_image_pollinations(
    prompt: str,
    style: str,
    aspect_ratio: str = "1:1",
    seed: int = 42
) -> dict[str, str | bytes]:
    """
    Generates a free image using Pollinations.ai (Flux model) GET endpoint.
    Requires no API keys or registration.
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
    
    try:
        response = requests.get(url, timeout=40)
        if response.ok:
            return {
                "image_bytes": response.content,
                "mime_type": "image/jpeg",
                "image_url": url,
                "is_fallback": False
            }
        else:
            raise RuntimeError(f"Pollinations API retorno codigo {response.status_code}")
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
            response = requests.get(fallback_url, timeout=35)
            if response.ok:
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
