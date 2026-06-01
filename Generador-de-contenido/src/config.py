from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv(override=True)

DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_STABILITY_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
DEFAULT_A2E_API_URL = "https://video.a2e.ai"
STATS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comparison_stats.json")


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "No se encontró GEMINI_API_KEY. Crea un archivo .env con tu clave de Gemini."
        )
    return api_key


def has_gemini_api_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def get_text_model() -> str:
    return os.getenv("GEMINI_TEXT_MODEL", DEFAULT_TEXT_MODEL)


def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def has_openai_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def get_openai_model() -> str:
    return os.getenv("OPENAI_TEXT_MODEL", DEFAULT_OPENAI_MODEL)


def get_stability_api_key() -> str:
    api_key = os.getenv("STABILITY_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "No se encontró STABILITY_API_KEY. Agrega tu clave de Stability AI en el archivo .env."
        )
    return api_key


def has_stability_api_key() -> bool:
    return bool(os.getenv("STABILITY_API_KEY", "").strip())


def get_stability_api_url() -> str:
    return os.getenv("STABILITY_API_URL", DEFAULT_STABILITY_API_URL).strip()


def get_a2e_api_key() -> str:
    return os.getenv("A2E_API_KEY", "").strip()


def has_a2e_api_key() -> bool:
    return bool(os.getenv("A2E_API_KEY", "").strip())


def get_a2e_api_url() -> str:
    return os.getenv("A2E_API_URL", DEFAULT_A2E_API_URL).strip()

