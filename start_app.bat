@echo off
title Local AI Document Studio

echo Starting Ollama Server...
start cmd /k "ollama serve"

timeout /t 10

echo Starting UI...
python ui.py

pause