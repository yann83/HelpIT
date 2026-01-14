@echo off
REM Script to compile HelpIT with admin elevation
REM This script uses PyInstaller to create a one-file executable

echo ========================================
echo  HelpIT Compilation Script
echo ========================================
echo.

REM Clean previous build
echo [INFO] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist HelpIT.exe del /f /q HelpIT.exe

echo [INFO] Starting compilation...
echo.

REM Compile using the spec file
pyinstaller helpit_debug.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Compilation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Compilation successful!
echo ========================================
echo.
echo Executable location: dist\HelpIT.exe
echo.
echo The executable will request admin privileges when launched.
echo.

pause
