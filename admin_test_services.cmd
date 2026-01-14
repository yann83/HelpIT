@echo off
REM --- Modifier ces chemins en fonction de votre projet ---

REM Chemin vers le répertoire de votre projet (où se trouve le dossier venv)
set "PROJECT_DIR=C:\CONFIDENTIEL\PROJETS\HelpIT"

REM Nom de votre environnement virtuel (souvent 'venv')
set "VENV_NAME=.venv"

REM Nom de votre script Python à exécuter
set "PYTHON_SCRIPT=test_services.py"

REM --------------------------------------------------------

cd /d "%PROJECT_DIR%"

REM Active l'environnement virtuel
call "%VENV_NAME%\Scripts\activate.bat"

REM Exécute le script Python
python "%PYTHON_SCRIPT%"

REM Désactive l'environnement virtuel (optionnel, si vous voulez que la console reste active)
REM deactivate

echo.
echo Script %PYTHON_SCRIPT% terminé.
pause
