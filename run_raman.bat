@echo off
chcp 65001 >nul
TITLE Laboratorio CÓDICE - Espectroscopia Raman | CNCPC - INAH
echo ======================================================================
echo    🔬 Laboratorio CÓDICE - Espectroscopia Raman | CNCPC - INAH
echo ======================================================================
echo.

IF NOT EXIST .venv (
    echo [INFO] Creando entorno virtual .venv...
    python -m venv .venv
)

echo [INFO] Activando entorno virtual e instalando dependencias...
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo.
echo [INFO] Iniciando Raman SpectroLab Pro...
python raman_analysis.py
pause
