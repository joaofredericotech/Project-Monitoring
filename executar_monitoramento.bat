@echo off
echo REM  © 2026 Joao Frederico ^| Projeto: Monitoramento de Sistemas
pause
cd /d "%~dp0"

echo Instalando/confirmando dependencias...
python -m pip install playwright
python -m playwright install chromium

echo.
echo Iniciando monitoramento...
python monitorar.py

pause