@echo off
chcp 65001 >nul
title Test de rentree - le PC du professeur
cd /d "%~dp0"
echo ============================================================
echo   TEST DE RENTREE - le PC lance les tests et recoit tout
echo ============================================================
echo.
echo Le poste de commande s'ouvre dans le navigateur.
echo NE PAS FERMER cette fenetre pendant le test. Pour arreter : la fermer.
echo.
python -c "import qrcode" 2>nul
if errorlevel 1 (
  echo Module QR code absent : installation, une seule fois, si Internet est la...
  python -m pip install --user --quiet "qrcode[pil]" 2>nul
)
rem Le raccourci du Bureau se (re)pose a chaque lancement : utile sur l'autre poste.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$n='Test de rentr'+[char]0xE9+'e.lnk'; $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) $n)); $s.TargetPath='%~dp0Test-de-rentree.cmd'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0test-de-rentree.ico,0'; $s.Description='Un clic : le PC lance les tests sur telephone et recoit tout'; $s.Save()" >nul 2>nul
python serveur-test-accueil.py 8765 --ouvrir /prof
pause
