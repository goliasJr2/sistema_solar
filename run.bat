@echo off
title Simulador Astronomico 3D - Grupo 1
cd /d "%~dp0"
echo A iniciar o Simulador Astronomico 3D...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
