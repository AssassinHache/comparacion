from __future__ import annotations

CONTENT_TYPES = [
    "Historia corta",
    "Poema",
    "Descripción de producto",
]

STYLES = [
    "Fantasía",
    "Ciencia ficción",
    "Marketing",
]

QUICK_PROMPTS = [
    "Una ciudad flotante donde los relojes predicen emociones.",
    "Un perfume inteligente diseñado para viajeros espaciales.",
    "Una espada antigua que traduce los sueños de su portador.",
]


def build_text_prompt(
    user_prompt: str,
    content_type: str,
    style: str,
    length: int,
) -> str:
    style_guides = {
        "Fantasía": "usa imágenes evocadoras, un tono mágico y detalles sensoriales.",
        "Ciencia ficción": "emplea ideas futuristas, tecnología sugerente y un tono inmersivo.",
        "Marketing": "escribe con claridad persuasiva, beneficios concretos y gancho comercial.",
    }

    content_guides = {
        "Cuento": "Escribe una historia breve con inicio, desarrollo y cierre satisfactorio.",
        "Historia corta": "Escribe una historia breve con inicio, desarrollo y cierre satisfactorio.",
        "Poema": "Escribe un poema con ritmo natural, imágenes potentes y cierre memorable.",
        "Artículo": "Escribe un artículo crítico bien estructurado con una introducción, desarrollo y conclusión.",
        "Marketing Copy": "Escribe una descripción de producto atractiva, útil y orientada a resaltar valor comercial."
    }

    selected_style = style_guides.get(style, "escribe con tono claro y coherente.")
    selected_content = content_guides.get(content_type, "Escribe un texto creativo estructurado.")

    return f"""
Eres un asistente de escritura creativa en español.

Tarea:
- Genera un(a) {content_type.lower()} en español.
- El estilo o nicho principal es: {style}.
- La extensión objetivo es de aproximadamente {length} palabras.
- Mantén un tono coherente con el estilo elegido.
- Evita listas, encabezados y explicaciones meta.
- Entrega solo el texto final.

Guía de contenido:
- {selected_content}

Guía de estilo:
- {selected_style}

Idea base del usuario:
{user_prompt.strip()}
""".strip()

