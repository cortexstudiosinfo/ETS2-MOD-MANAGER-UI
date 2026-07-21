@echo off
title Truck Mod Manager — Console
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================================
echo  Truck Mod Manager -- Dev Launcher
echo ============================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo         Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [*] Using: %PYVER%

:: Create venv if missing
if not exist "venv\" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate venv
call venv\Scripts\activate.bat

:: Upgrade pip and clear corrupt cache
echo [*] Upgrading pip...
python -m pip install --upgrade pip -q --disable-pip-version-check --no-cache-dir

echo [*] Clearing pip cache...
pip cache purge >nul 2>&1

:: Install dependencies
echo [*] Installing dependencies...
pip install --disable-pip-version-check --no-cache-dir -q -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [!] pip install failed. Recreating virtual environment...
    call venv\Scripts\deactivate.bat 2>nul
    rmdir /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip -q --disable-pip-version-check --no-cache-dir
    pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Could not install dependencies. Check requirements.txt or internet.
        pause
        exit /b 1
    )
)

echo.
echo [*] Starting app -- log output below (also saved to log.txt)
echo ============================================================
echo.

python main.py

echo.
echo ============================================================
echo  App exited. Check above or log.txt for any errors.
echo ============================================================
pause
