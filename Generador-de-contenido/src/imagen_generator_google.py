from __future__ import annotations

import base64
from io import BytesIO
from google import genai
from google.genai import types
from src.config import get_gemini_api_key

# Standard premium images for mock mode based on keywords in prompt or style
MOCK_IMAGEN_IMAGES = {
    "Fantasía": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=600&auto=format&fit=crop", # Magical forest
    "Ciencia ficción": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop", # Space nebula
    "Marketing": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop", # Dashboard/clean
    "default": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=600&auto=format&fit=crop" # Beach
}

def generate_image_google(
    prompt: str,
    style: str,
    aspect_ratio: str = "1:1",
    api_key: str | None = None
) -> dict[str, str | bytes]:
    """
    Generates an image using Google's Imagen 3.0 API via the new google-genai SDK.
    Falls back to active generation using Pollinations Flux or a safe Imagen prompt if it fails.
    """
    client = None
    mapped_ratio = "1:1"
    
    # 1. Google Imagen 3 aspect ratios mapping
    ratio_mapping = {
        "1:1": "1:1",
        "16:9": "16:9",
        "9:16": "9:16",
        "4:3": "4:3",
        "3:4": "3:4"
    }
    mapped_ratio = ratio_mapping.get(aspect_ratio, "1:1")

    if not api_key:
        try:
            api_key = get_gemini_api_key()
        except ValueError:
            # Fallback to Pollinations active generation if no Google key is available!
            print("No se encontró API key de Google Gemini. Generando activamente con Pollinations Flux...")
            try:
                from src.imagen_generator_pollinations import generate_image_pollinations
                res = generate_image_pollinations(prompt, style, aspect_ratio, seed=77)
                res["is_fallback"] = True
                return res
            except Exception as pollinations_exc:
                print(f"Error calling Pollinations as fallback for missing key: {pollinations_exc}")
                return {
                    "image_bytes": b"",
                    "mime_type": "image/jpeg",
                    "image_url": "",
                    "is_fallback": True
                }

    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=f"{prompt}, high quality, style: {style}",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=mapped_ratio,
                output_mime_type="image/jpeg"
            )
        )
        
        if response.generated_images:
            img_data = response.generated_images[0].image.image_bytes
            return {
                "image_bytes": img_data,
                "mime_type": "image/jpeg",
                "image_url": "",
                "is_fallback": False
            }
        else:
            raise RuntimeError("Imagen 3 no devolvió ninguna imagen.")
            
    except Exception as exc:
        print(f"Error calling Google Imagen 3 con prompt original: {exc}")
        
        # FIRST ATTEMPT: Try to actively generate the ORIGINAL prompt using Pollinations Flux as a free, high-quality cascade generator
        print("Intentando generar prompt original con Pollinations Flux...")
        try:
            from src.imagen_generator_pollinations import generate_image_pollinations
            res = generate_image_pollinations(prompt, style, aspect_ratio, seed=77)
            # Mark is_fallback to False because it successfully generated the original requested prompt (e.g. the dog)!
            res["is_fallback"] = False
            return res
        except Exception as pollinations_exc:
            print(f"No se pudo generar prompt original con Pollinations: {pollinations_exc}. Procediendo con prompts seguros...")
        
        # SECOND ATTEMPT: If Pollinations fails to generate the original, use predefined safe prompts
        SAFE_FALLBACK_PROMPTS = {
            "Fantasía": "A beautiful fantasy landscape with a glowing magical river, majestic mountains, detailed digital art",
            "Ciencia ficción": "A futuristic space station orbiting a beautiful planet, sci-fi cinematic composition",
            "Marketing": "A premium minimalist workspace with a modern laptop, soft studio lighting, clean background",
            "default": "A beautiful tropical sunset over a calm ocean, high quality landscape photography"
        }
        
        fallback_prompt = SAFE_FALLBACK_PROMPTS.get(style, SAFE_FALLBACK_PROMPTS["default"])
        
        try:
            # Third attempt: Try to actively generate the safe prompt with Google Imagen 3 if client is set up
            if client:
                response = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=fallback_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=mapped_ratio,
                        output_mime_type="image/jpeg"
                    )
                )
                if response.generated_images:
                    img_data = response.generated_images[0].image.image_bytes
                    return {
                        "image_bytes": img_data,
                        "mime_type": "image/jpeg",
                        "image_url": "",
                        "is_fallback": True
                    }
        except Exception as inner_exc:
            print(f"Error en generación activa con Google Imagen 3 de respaldo: {inner_exc}")
            
        # Fourth attempt: If Google Imagen generation fails completely, actively generate safe prompt via Pollinations Flux!
        print("Intentando generación de respaldo activa con Pollinations Flux...")
        try:
            from src.imagen_generator_pollinations import generate_image_pollinations
            res = generate_image_pollinations(fallback_prompt, style, aspect_ratio, seed=77)
            res["is_fallback"] = True
            return res
        except Exception as pollinations_inner_exc:
            print(f"Error en generación activa final con Pollinations: {pollinations_inner_exc}")
            
        return {
            "image_bytes": b"",
            "mime_type": "image/jpeg",
            "image_url": "",
            "is_fallback": True
        }
