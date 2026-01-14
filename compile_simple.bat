@echo off
REM Simple compilation script with admin elevation
REM This compiles directly without using a spec file

echo ========================================
echo  HelpIT Quick Compilation
echo ========================================
echo.

REM Install PyInstaller if needed
REM python -m pip install pyinstaller --upgrade

REM Compile with manifest
pyinstaller --onefile ^
    --windowed ^
    --name HelpIT ^
    --icon=helpit.ico ^
    --manifest=helpit.manifest ^
    --add-data "config.json;." ^
    --add-data "bin/PsExec64.exe;bin" ^
    main.py

echo.
echo Compilation complete!
echo Executable: dist\HelpIT.exe
echo.
pause
