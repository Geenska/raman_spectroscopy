#!/usr/bin/env bash
echo "========================================================"
echo "       🔬 Raman SpectroLab Pro - CNCPC / CÓDICE"
echo "========================================================"
echo

if [ ! -d ".venv" ]; then
    echo "[INFO] Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

echo "[INFO] Activando entorno virtual e instalando dependencias..."
source .venv/bin/activate
pip install -q -r requirements.txt

echo
echo "[INFO] Iniciando Raman SpectroLab Pro..."
python raman_analysis.py
