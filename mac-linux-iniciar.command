#!/bin/bash

# Ejecutalo en la terminal, en la carpeta del proyecto. O simplemente doble click.
# Este script inicia el backend de Python y el frontend de Node.js
# Asegúrate de que LM Studio esté ejecutándose antes de ejecutar este script.

echo "========================================================="
echo "** ATENCIÓN: Asegúrate que LM Studio esté ejecutándose. **"
echo "========================================================="
echo ""

# 1. Iniciar el Backend (Python) en segundo plano
echo "1. Iniciando el Backend (app.py)..."
python3 app.py &

# Guardar el ID del proceso del backend para poder terminarlo más tarde si es necesario
BACKEND_PID=$!

# 2. Iniciar el Frontend (Node.js)
echo "2. Iniciando el Frontend (npm start)..."
cd frontend
npm start