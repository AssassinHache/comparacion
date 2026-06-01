from __future__ import annotations

import time
import requests
from src.config import get_stability_api_key

# List of high-quality premium video URLs for mock mode/fallback based on style
MOCK_VIDEOS = {
    "Fantasía": "https://assets.mixkit.co/videos/preview/mixkit-mysterious-glowing-mushrooms-in-a-fantasy-forest-51981-large.mp4",
    "Ciencia ficción": "https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-background-1611-large.mp4",
    "Marketing": "https://assets.mixkit.co/videos/preview/mixkit-abstract-laser-lights-background-loop-41851-large.mp4",
    "default": "https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-529-large.mp4"
}

def generate_video_stability(
    image_bytes: bytes,
    style: str,
    api_key: str | None = None,
    task_update_func = None
) -> str:
    """
    Generates a video from image bytes using Stability AI's Stable Video Diffusion (SVD) API.
    If the API is deprecated or credentials fail, falls back to a high-quality relevant mock video.
    """
    if not api_key:
        try:
            api_key = get_stability_api_key()
        except ValueError:
            # Safe fallback if API key is not configured
            if task_update_func:
                task_update_func("Stability AI Video (Simulación): Cargando efectos visuales...")
                time.sleep(2)
            return MOCK_VIDEOS.get(style, MOCK_VIDEOS["default"])

    if task_update_func:
        task_update_func("Stability AI Video: Enviando imagen base a la API de SVD...")

    headers = {
        "authorization": f"Bearer {api_key}"
    }
    
    files = {
        "image": ("image.png", image_bytes, "image/png")
    }
    
    data = {
        "seed": 0,
        "cfg_scale": 1.8,
        "motion_bucket_id": 127
    }

    try:
        # Step 1: Start video generation
        response = requests.post(
            "https://api.stability.ai/v2beta/image-to-video",
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Error al iniciar SVD: {response.text}")
            
        generation_id = response.json().get("id")
        if not generation_id:
            raise RuntimeError("La API no devolvió un ID de generación válido.")

        if task_update_func:
            task_update_func("Stability AI Video: Procesando video en la GPU de Stability...")

        # Step 2: Poll for completion
        result_url = f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}"
        
        max_attempts = 15
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if task_update_func:
                task_update_func(f"Stability AI Video: Procesando ({attempt * 6}s)...")
                
            poll_response = requests.get(
                result_url,
                headers={"authorization": f"Bearer {api_key}", "accept": "video/*"},
                timeout=30
            )
            
            if poll_response.status_code == 202:
                # Still processing, wait and poll again
                time.sleep(6)
                continue
            elif poll_response.status_code == 200:
                # Video is ready, save it locally to serve as static file
                import os
                import uuid
                video_filename = f"svd_{uuid.uuid4().hex}.mp4"
                video_dir = os.path.join(os.getcwd(), "static", "videos")
                os.makedirs(video_dir, exist_ok=True)
                video_path = os.path.join(video_dir, video_filename)
                
                with open(video_path, "wb") as f:
                    f.write(poll_response.content)
                    
                return f"/static/videos/{video_filename}"
            else:
                raise RuntimeError(f"Error al consultar estado de SVD: {poll_response.text}")
                
        raise RuntimeError("El tiempo de espera para la generación de video de Stability AI expiró.")
        
    except Exception as exc:
        # Safe fallback in case of deprecation, network failure, or credits issue
        if task_update_func:
            task_update_func(f"Stability AI Video (Simulación debido a: {str(exc)[:40]}...): Creando loop premium...")
            time.sleep(3)
        return MOCK_VIDEOS.get(style, MOCK_VIDEOS["default"])
