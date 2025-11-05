@echo off
title Iniciar Asistente Tecnico - Backend y Frontend

echo.
echo =========================================================
echo ** ATENCION: Asegurate que LM Studio este ejecutandose. **
echo =========================================================
echo.

echo 1. Iniciando el Backend (app.py)...
start /B cmd /k "python app.py"

echo 2. Iniciando el Frontend (npm start)...
cd frontend
start cmd /k "npm start"

echo.
echo ** Proceso de inicio completado. **
echo.

exit