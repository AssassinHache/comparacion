#!/bin/bash

# Script to run both Backend (FastAPI) and Frontend (Vite) concurrently

# Function to clean up background processes on exit
cleanup() {
    echo -e "\n\n\033[1;33m[+] Deteniendo servidores...\033[0m"
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit 0
}

# Trap Ctrl+C (SIGINT) and exit (SIGTERM)
trap cleanup SIGINT SIGTERM

echo -e "\033[1;36m====================================================="
echo -e "         INICIANDO ANTIGRAVITY ARENA"
echo -e "=====================================================\033[0m"

# 1. Start Backend (FastAPI)
echo -e "\033[1;34m[+] Iniciando Backend (FastAPI en http://127.0.0.1:8000)...\033[0m"
cd Generador-de-contenido || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Uvicorn
uvicorn app:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a second for backend to spin up
sleep 1.5

# 2. Start Frontend (Vite)
echo -e "\033[1;35m[+] Iniciando Frontend (Vite)...\033[0m"
cd front_generate || exit 1
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\033[1;32m====================================================="
echo -e "  ¡Servidores en ejecución!"
echo -e "  - Backend: http://127.0.0.1:8000"
echo -e "  - Frontend: Revisa la URL provista por Vite arriba"
echo -e "  Presiona Ctrl+C para detener ambos servidores."
echo -e "=====================================================\033[0m"

# Keep the script running
wait
