@echo off
title Simulador Astronomico 3D - Grupo 1
echo A iniciar o Simulador Astronomico 3D...
"C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
