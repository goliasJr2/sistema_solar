@echo off
title Simulador Astronomico 3D - Grupo 1
echo A iniciar o Simulador Astronomico 3D...
if exist "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" main.py
) else if exist "C:\pyenv\simulador\Scripts\python.exe" (
    C:\pyenv\simulador\Scripts\python.exe main.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
