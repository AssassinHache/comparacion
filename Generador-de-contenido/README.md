# Generación de Contenido Creativo Asistida por IA

Aplicación web construida con Streamlit que genera texto creativo a partir de una idea base del usuario y crea una imagen relacionada. La app usa Gemini para texto y Stability AI para imágenes.

## Características

- Generación de historias cortas, poemas y descripciones de producto.
- Selección de estilo o nicho: Fantasía, Ciencia ficción o Marketing.
- Control de longitud del texto mediante slider.
- Generación de imagen con Stable Image Ultra.
- Selección de relación de aspecto para la imagen.
- Historial reciente.
- Descarga del texto generado.
- Descarga de la imagen generada.
- Manejo claro de errores cuando falta la API key o falla la API.


## Requisitos

- Python 3.11 o superior
- Una API key válida de Gemini
- Una API key válida de Stability AI
- Acceso a internet para consumir la API

## Instalación paso a paso

1. Clona o descarga este proyecto.
2. Entra a la carpeta del proyecto.
3. Crea y activa un entorno virtual.

En Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

4. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración del archivo `.env`

1. Copia el archivo de ejemplo:

```bash
copy .env.example .env
```

Si usas macOS o Linux:

```bash
cp .env.example .env
```

2. Edita `.env` y agrega tu clave:

```env
GEMINI_API_KEY=tu_api_key_real
GEMINI_TEXT_MODEL=gemini-2.5-flash
STABILITY_API_KEY=tu_stability_api_key_real
STABILITY_API_URL=https://api.stability.ai/v2beta/stable-image/generate/ultra

```

El modelo de texto es configurable. La generación de imagen usa el endpoint oficial `POST /v2beta/stable-image/generate/ultra` de Stability AI.

## Ejecución de la app

Con el entorno virtual activo y el `.env` configurado:

```bash
streamlit run app.py
```

Luego abre en el navegador la URL local que Streamlit muestre en la terminal.

## Cómo funciona

1. El usuario escribe una idea base.
2. La app construye un prompt enriquecido en español.
3. Se genera primero el texto con.
4. Se resume el contenido visual del texto generado.
5. Se construye un prompt visual breve en inglés para cumplir con Stability AI.
6. Se genera la imagen con Stability AI.
7. Se muestran texto e imagen en la interfaz.

Gracias ING 🫡
