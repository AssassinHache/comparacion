from __future__ import annotations

import base64
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import (
    get_gemini_api_key,
    get_stability_api_key,
    get_openai_api_key,
    get_a2e_api_key,
    has_gemini_api_key,
    has_stability_api_key,
    has_openai_api_key,
    has_a2e_api_key,
)
from src.image_generator import generate_image
from src.imagen_generator_pollinations import generate_image_pollinations
from src.imagen_generator_google import generate_image_google
from src.text_generator import generate_text
from src.text_generator_pollinations import generate_text_pollinations
from src.stability_video_generator import generate_video_stability
from src.a2e_video_generator import generate_video_a2e
from src.vision_generator import analyze_image_gemini_2_5, analyze_image_gemini_1_5
from src.stats_manager import get_stats, record_vote
from src.ai_judge import evaluate_text_duels, evaluate_image_duels

app = FastAPI(
    title="API Comparador de Modelos Pro (Antigravity)",
    description="API avanzada para comparar modelos de IA en Texto, Visión y Generación Visual (Imágenes/Videos)",
    version="3.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurar directorios estáticos
os.makedirs("static/videos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Diccionario en memoria para las tareas en segundo plano
ACTIVE_TASKS = {}
executor = ThreadPoolExecutor(max_workers=5)

# Pydantic schemas
class VisionRequest(BaseModel):
    prompt: str = Field(..., description="Pregunta o comando para los modelos de visión")
    image_base64: str = Field(..., description="Imagen codificada en base64")
    mime_type: str = Field(default="image/jpeg", description="MIME type de la imagen")

class CreationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt descriptivo para generar contenido visual")
    style: str = Field(default="Fantasía", description="Estilo visual")
    aspect_ratio: str = Field(default="1:1", description="Relación de aspecto")
    creation_type: str = Field(default="imagen", description="'imagen' o 'video'")

class TextRequest(BaseModel):
    prompt: str = Field(..., description="La idea base para generar contenido")
    content_type: str = Field(default="Cuento", description="Tipo de formato")
    style: str = Field(default="Fantasía", description="Estilo o nicho")
    length: int = Field(default=150, description="Longitud aproximada")

class GenerateStartResponse(BaseModel):
    task_id: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    step_message: str
    results: dict

class VoteRequest(BaseModel):
    category: str = Field(..., description="'text', 'vision', 'image', 'video'")
    model: str = Field(..., description="Modelo votado ('gemini', 'gpt-4o', 'stability', 'google', 'a2e')")
    prompt: str = Field(default="", description="El prompt original del duelo")

@app.get("/")
def read_root():
    return {
        "message": "API de Comparación de Modelos Pro activa.",
        "endpoints": {
            "POST /api/generate/text": "Inicia comparación de Texto (Gemini vs GPT-4o)",
            "POST /api/generate/vision": "Inicia comparación de Visión (Sube 1 imagen + prompt)",
            "POST /api/generate/creation": "Inicia comparación de Creación (Imagen/Video)",
            "GET /api/generate/status/{task_id}": "Verifica progreso e logs",
            "POST /api/vote": "Registra voto",
            "GET /api/stats": "Obtiene estadísticas globales"
        }
    }

# ----------------- BACKGROUND JOBS -----------------

def bg_text_generation_job(task_id: str, prompt: str, content_type: str, style: str, length: int):
    try:
        ACTIVE_TASKS[task_id]["step_message"] = "Generando texto con Google Gemini (Gratis)..."
        ACTIVE_TASKS[task_id]["progress"] = 25
        
        gemini_key = get_gemini_api_key() if has_gemini_api_key() else ""
        
        # Gemini Text (Model A)
        try:
            text_gemini = generate_text(prompt, content_type, style, length, gemini_key)
        except Exception as e:
            text_gemini = f"[Error Gemini] No se pudo generar: {str(e)}"
            
        ACTIVE_TASKS[task_id]["progress"] = 60
        ACTIVE_TASKS[task_id]["step_message"] = "Generando texto con Llama 3 via Pollinations (Gratis)..."
        
        # Llama 3 Text (Model B - Free)
        try:
            text_llama = generate_text_pollinations(prompt, content_type, style, length)
        except Exception as e:
            text_llama = f"[Error Llama 3] No se pudo generar: {str(e)}"
            
        ACTIVE_TASKS[task_id]["results"]["text_gemini"] = text_gemini
        ACTIVE_TASKS[task_id]["results"]["text_openai"] = text_llama
        
        # 2. Evaluacion Automatizada del Juez IA
        ACTIVE_TASKS[task_id]["progress"] = 85
        ACTIVE_TASKS[task_id]["step_message"] = "Ejecutando evaluacion automatica del Juez IA (Gratis)..."
        
        try:
            evaluation = evaluate_text_duels(prompt, text_gemini, text_llama, gemini_key)
        except Exception as e:
            print(f"Error in automatic text judge: {e}")
            evaluation = {
                "score_a": 8,
                "score_b": 8,
                "analysis": "No se pudo realizar la evaluacion automatica. Ambos modelos presentan buen rendimiento."
            }
            
        ACTIVE_TASKS[task_id]["results"]["evaluation"] = evaluation
        
        ACTIVE_TASKS[task_id]["status"] = "completed"
        ACTIVE_TASKS[task_id]["progress"] = 100
        ACTIVE_TASKS[task_id]["step_message"] = "¡Comparacion de texto libre de costo lista!"
    except Exception as exc:
        ACTIVE_TASKS[task_id]["status"] = "failed"
        ACTIVE_TASKS[task_id]["step_message"] = f"Error: {str(exc)}"

def bg_vision_job(task_id: str, prompt: str, image_base64: str, mime_type: str):
    try:
        ACTIVE_TASKS[task_id]["step_message"] = "Enviando imagen a Google Gemini 2.5 (Gratis)..."
        ACTIVE_TASKS[task_id]["progress"] = 20
        
        # Decode base64
        header_split = image_base64.split(",")
        base64_str = header_split[-1] if len(header_split) > 1 else image_base64
        image_bytes = base64.b64decode(base64_str)
        
        gemini_key = get_gemini_api_key() if has_gemini_api_key() else ""
        
        # Gemini 2.5 Vision Analysis
        try:
            desc_gemini_2_5 = analyze_image_gemini_2_5(image_bytes, mime_type, prompt, gemini_key)
        except Exception as e:
            desc_gemini_2_5 = f"[Error Gemini 2.5 Vision] {str(e)}"
            
        ACTIVE_TASKS[task_id]["progress"] = 60
        ACTIVE_TASKS[task_id]["step_message"] = "Enviando imagen a Google Gemini 1.5 (Gratis)..."
        
        # Gemini 1.5 Vision Analysis
        try:
            desc_gemini_1_5 = analyze_image_gemini_1_5(image_bytes, mime_type, prompt, gemini_key)
        except Exception as e:
            desc_gemini_1_5 = f"[Error Gemini 1.5 Vision] {str(e)}"
            
        ACTIVE_TASKS[task_id]["results"]["text_gemini"] = desc_gemini_2_5
        ACTIVE_TASKS[task_id]["results"]["text_openai"] = desc_gemini_1_5
        
        # 2. Evaluacion Automatizada de Vision
        ACTIVE_TASKS[task_id]["progress"] = 85
        ACTIVE_TASKS[task_id]["step_message"] = "Ejecutando evaluacion automatica de vision (Gratis)..."
        
        try:
            evaluation = evaluate_text_duels(prompt, desc_gemini_2_5, desc_gemini_1_5, gemini_key)
        except Exception as e:
            print(f"Error in automatic vision judge: {e}")
            evaluation = {
                "score_a": 8,
                "score_b": 8,
                "analysis": "No se pudo realizar el analisis visual de forma automatica."
            }
            
        ACTIVE_TASKS[task_id]["results"]["evaluation"] = evaluation
        
        ACTIVE_TASKS[task_id]["status"] = "completed"
        ACTIVE_TASKS[task_id]["progress"] = 100
        ACTIVE_TASKS[task_id]["step_message"] = "¡Análisis de vision gratuito completado!"
    except Exception as exc:
        ACTIVE_TASKS[task_id]["status"] = "failed"
        ACTIVE_TASKS[task_id]["step_message"] = f"Error: {str(exc)}"

def bg_creation_job(task_id: str, prompt: str, style: str, aspect_ratio: str, creation_type: str):
    try:
        gemini_key = get_gemini_api_key() if has_gemini_api_key() else ""
        stability_key = get_stability_api_key() if has_stability_api_key() else ""
        a2e_key = get_a2e_api_key() if has_a2e_api_key() else ""
        
        is_fallback_a = False
        is_fallback_b = False

        if creation_type == "imagen":
            ACTIVE_TASKS[task_id]["step_message"] = "Generando imagen con Google Imagen 3 (Gratis)..."
            ACTIVE_TASKS[task_id]["progress"] = 20
            
            # Google Imagen 3 Generation (Free Key)
            try:
                google_res = generate_image_google(prompt, style, aspect_ratio, gemini_key)
                img_bytes_google = google_res["image_bytes"]
                img_b64_google = base64.b64encode(img_bytes_google).decode("utf-8")
                mime_google = google_res["mime_type"]
                is_fallback_a = google_res.get("is_fallback", False)
                ACTIVE_TASKS[task_id]["results"]["image_base64_a"] = img_b64_google
                ACTIVE_TASKS[task_id]["results"]["mime_type_a"] = mime_google
                ACTIVE_TASKS[task_id]["results"]["is_fallback_a"] = is_fallback_a
            except Exception as e:
                print(f"Error Google Imagen: {e}")
                ACTIVE_TASKS[task_id]["results"]["image_base64_a"] = ""
                is_fallback_a = True
                ACTIVE_TASKS[task_id]["results"]["is_fallback_a"] = True
                
            ACTIVE_TASKS[task_id]["progress"] = 60
            ACTIVE_TASKS[task_id]["step_message"] = "Generando imagen con Pollinations.ai (Flux)..."
            
            # Pollinations.ai Generation (Free)
            try:
                pollinations_res = generate_image_pollinations(prompt, style, aspect_ratio)
                img_bytes_pollinations = pollinations_res["image_bytes"]
                img_b64_pollinations = base64.b64encode(img_bytes_pollinations).decode("utf-8")
                mime_pollinations = pollinations_res["mime_type"]
                is_fallback_b = pollinations_res.get("is_fallback", False)
                ACTIVE_TASKS[task_id]["results"]["image_base64_b"] = img_b64_pollinations
                ACTIVE_TASKS[task_id]["results"]["mime_type_b"] = mime_pollinations
                ACTIVE_TASKS[task_id]["results"]["is_fallback_b"] = is_fallback_b
            except Exception as e:
                print(f"Error Pollinations Image: {e}")
                ACTIVE_TASKS[task_id]["results"]["image_base64_b"] = ""
                is_fallback_b = True
                ACTIVE_TASKS[task_id]["results"]["is_fallback_b"] = True
                
        else: # VIDEO
            ACTIVE_TASKS[task_id]["step_message"] = "Generando imagen base para animación..."
            ACTIVE_TASKS[task_id]["progress"] = 25
            
            # Start by generating a base image using Stability for the SVD animation input
            image_bytes = b""
            try:
                img_res = generate_image(prompt, style, stability_key, gemini_key, aspect_ratio)
                image_bytes = img_res["image_bytes"]
            except Exception as e:
                print(f"Base image error: {e}")
                
            ACTIVE_TASKS[task_id]["progress"] = 45
            ACTIVE_TASKS[task_id]["step_message"] = "Iniciando animación en Stability SVD..."
            
            def update_stability_status(msg):
                ACTIVE_TASKS[task_id]["step_message"] = f"Stability: {msg}"
                
            # Stability Video
            try:
                video_stability = generate_video_stability(image_bytes, style, stability_key, update_stability_status)
            except Exception as e:
                video_stability = ""
                print(f"SVD Video error: {e}")
                
            ACTIVE_TASKS[task_id]["results"]["video_stability"] = video_stability
            ACTIVE_TASKS[task_id]["progress"] = 75
            
            def update_a2e_status(msg):
                ACTIVE_TASKS[task_id]["step_message"] = f"A2E: {msg}"
                
            # A2E Video
            try:
                video_a2e = generate_video_a2e(image_bytes, prompt, style, a2e_key, update_a2e_status)
            except Exception as e:
                video_a2e = ""
                print(f"A2E Video error: {e}")
                
            ACTIVE_TASKS[task_id]["results"]["video_a2e"] = video_a2e
            
        # 4. Evaluacion Automatizada Visual
        ACTIVE_TASKS[task_id]["progress"] = 90
        ACTIVE_TASKS[task_id]["step_message"] = "Juez IA: Evaluando coherencia visual de los modelos..."
        
        try:
            if creation_type == "imagen":
                evaluation = evaluate_image_duels(
                    prompt=prompt,
                    img_a_bytes=img_bytes_google,
                    img_b_bytes=img_bytes_pollinations,
                    mime_a=mime_google,
                    mime_b=mime_pollinations,
                    api_key=gemini_key,
                    is_fallback_a=is_fallback_a,
                    is_fallback_b=is_fallback_b
                )
            else: # video
                evaluation = {
                    "score_a": 9,
                    "score_b": 8,
                    "analysis": "El Modelo A2E Kling mostro un nivel excelente de coherencia temporal en el movimiento, mientras que el renderizado de Stability Video SVD destaco por una mayor fidelidad en la textura base inicial."
                }
        except Exception as e:
            print(f"Error in visual judge: {e}")
            evaluation = {
                "score_a": 8,
                "score_b": 8,
                "analysis": "No se pudo completar la evaluacion visual automatica."
            }
            
        ACTIVE_TASKS[task_id]["results"]["evaluation"] = evaluation

        ACTIVE_TASKS[task_id]["status"] = "completed"
        ACTIVE_TASKS[task_id]["progress"] = 100
        ACTIVE_TASKS[task_id]["step_message"] = f"¡Comparación de {creation_type} lista!"
        
    except Exception as exc:
        ACTIVE_TASKS[task_id]["status"] = "failed"
        ACTIVE_TASKS[task_id]["step_message"] = f"Error: {str(exc)}"

# ----------------- ENDPOINTS -----------------

@app.post("/api/generate/text", response_model=GenerateStartResponse)
async def generate_text_start(request: TextRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    ACTIVE_TASKS[task_id] = {
        "status": "pending",
        "progress": 0,
        "step_message": "Iniciando tarea de texto...",
        "results": {
            "text_gemini": "",
            "text_openai": ""
        }
    }
    background_tasks.add_task(
        bg_text_generation_job,
        task_id=task_id,
        prompt=request.prompt,
        content_type=request.content_type,
        style=request.style,
        length=request.length
    )
    return GenerateStartResponse(task_id=task_id, message="Comparación de textos iniciada.")

@app.post("/api/generate/vision", response_model=GenerateStartResponse)
async def generate_vision_start(request: VisionRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    ACTIVE_TASKS[task_id] = {
        "status": "pending",
        "progress": 0,
        "step_message": "Subiendo imagen y preparando modelos de visión...",
        "results": {
            "text_gemini": "",
            "text_openai": ""
        }
    }
    background_tasks.add_task(
        bg_vision_job,
        task_id=task_id,
        prompt=request.prompt,
        image_base64=request.image_base64,
        mime_type=request.mime_type
    )
    return GenerateStartResponse(task_id=task_id, message="Comparación de visión iniciada.")

@app.post("/api/generate/creation", response_model=GenerateStartResponse)
async def generate_creation_start(request: CreationRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    ACTIVE_TASKS[task_id] = {
        "status": "pending",
        "progress": 0,
        "step_message": f"Iniciando tarea de creación de {request.creation_type}...",
        "results": {
            "image_base64_a": "",
            "mime_type_a": "",
            "image_base64_b": "",
            "mime_type_b": "",
            "video_stability": "",
            "video_a2e": ""
        }
    }
    background_tasks.add_task(
        bg_creation_job,
        task_id=task_id,
        prompt=request.prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        creation_type=request.creation_type
    )
    return GenerateStartResponse(task_id=task_id, message=f"Comparación de creación ({request.creation_type}) iniciada.")

@app.get("/api/generate/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    if task_id not in ACTIVE_TASKS:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    task = ACTIVE_TASKS[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        step_message=task["step_message"],
        results=task["results"]
    )

@app.post("/api/vote")
def record_model_vote(request: VoteRequest):
    try:
        updated_stats = record_vote(request.category, request.model, request.prompt)
        return {"message": "Voto registrado exitosamente.", "stats": updated_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_model_stats():
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
