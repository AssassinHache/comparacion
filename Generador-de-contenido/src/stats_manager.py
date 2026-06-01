from __future__ import annotations

import json
import os
import time
from src.config import STATS_FILE_PATH

def init_stats() -> dict:
    return {
        "text_votes": {
            "gemini": 0,
            "gpt-4o": 0
        },
        "vision_votes": {
            "gemini": 0,
            "gpt-4o": 0
        },
        "image_votes": {
            "stability": 0,
            "google": 0
        },
        "video_votes": {
            "a2e": 0,
            "stability": 0
        },
        "total_comparisons": 0,
        "history": []
    }

def get_stats() -> dict:
    if not os.path.exists(STATS_FILE_PATH):
        stats = init_stats()
        save_stats(stats)
        return stats
    
    try:
        with open(STATS_FILE_PATH, "r", encoding="utf-8") as f:
            stats = json.load(f)
            # Guarantee backward compatibility
            default = init_stats()
            updated = False
            for key in default:
                if key not in stats:
                    stats[key] = default[key]
                    updated = True
                elif isinstance(default[key], dict):
                    for subkey in default[key]:
                        if subkey not in stats[key]:
                            stats[key][subkey] = default[key][subkey]
                            updated = True
            if updated:
                save_stats(stats)
            return stats
    except Exception:
        stats = init_stats()
        save_stats(stats)
        return stats

def save_stats(stats: dict) -> None:
    try:
        with open(STATS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"Error al guardar estadísticas: {exc}")

def record_vote(category: str, model_name: str, prompt: str = "") -> dict:
    """
    category: 'text', 'vision', 'image', 'video'
    model_name: 'gemini', 'gpt-4o', 'stability', 'google', 'a2e'
    prompt: El prompt original ingresado por el usuario
    """
    stats = get_stats()
    
    cat_key = f"{category}_votes"
    if cat_key in stats:
        if model_name in stats[cat_key]:
            stats[cat_key][model_name] += 1
            stats["total_comparisons"] += 1
            
    # Registrar en el historial de prompts
    if "history" not in stats:
        stats["history"] = []
        
    stats["history"].insert(0, {
        "prompt": prompt if prompt else "Prompt no especificado",
        "category": category,
        "winner": model_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    save_stats(stats)
    return stats
