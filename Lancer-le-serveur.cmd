@echo off
chcp 65001 >nul
title Tests sur telephone - serveur du professeur
cd /d "%~dp0"
echo ============================================================
echo   TESTS SUR TELEPHONE - le PC sert les pages et recoit tout
echo ============================================================
echo.
python -c "import qrcode" 2>nul
if errorlevel 1 (
  echo Module QR code absent : installation, une seule fois, si Internet est la...
  python -m pip install --user --quiet "qrcode[pil]" 2>nul
)
echo Le serveur demarre. NE PAS FERMER cette fenetre pendant le test.
echo Pour arreter : Ctrl+C, ou fermer la fenetre.
echo.
start "" "http://localhost:8765/projeter"
start "" "http://localhost:8765/resultats"
python serveur-test-accueil.py 8765
pause
