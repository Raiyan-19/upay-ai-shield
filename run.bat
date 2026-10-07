@echo off
setlocal

:: ============================================================================
:: upay AI Shield Enterprise — One-Click Automated Startup Script
:: Auto-detects virtual environment, runtime, environment variables, and ports.
:: ============================================================================

cd /d "%~dp0"
title upay AI Shield Enterprise

echo.
echo ============================================================================
echo   upay AI Shield Enterprise -- Starting Risk Intelligence Platform
echo ============================================================================
echo.

:: 1. Auto-detect and initialize .env from .env.example if missing
if not exist ".env" (
    if exist ".env.example" (
        echo [*] .env not found. Initializing from .env.example...
        copy ".env.example" ".env" >nul
        echo [OK] Created .env configuration.
    )
)

:: 2. Auto-detect Python virtual environment or system Python
set "PY_EXE="

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
    echo [*] Detected virtual environment: .venv
)

if "%PY_EXE%"=="" (
    if exist "venv\Scripts\python.exe" (
        set "PY_EXE=venv\Scripts\python.exe"
        echo [*] Detected virtual environment: venv
    )
)

:: If no existing virtual environment, try creating one automatically
if "%PY_EXE%"=="" (
    echo [*] No virtual environment detected. Setting up .venv...

    where uv >nul 2>nul
    if %errorlevel% equ 0 (
        echo [*] Initializing virtual environment with uv...
        uv venv .venv
        if exist ".venv\Scripts\python.exe" (
            set "PY_EXE=.venv\Scripts\python.exe"
            echo [*] Installing dependencies from requirements.txt via uv...
            uv pip install -r requirements.txt
        )
    )
)

if "%PY_EXE%"=="" (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        echo [*] Initializing virtual environment with py -3...
        py -3 -m venv .venv
        if exist ".venv\Scripts\python.exe" (
            set "PY_EXE=.venv\Scripts\python.exe"
            echo [*] Installing dependencies from requirements.txt...
            .venv\Scripts\python.exe -m pip install -r requirements.txt
        ) else (
            set "PY_EXE=py -3"
        )
    )
)

if "%PY_EXE%"=="" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        echo [*] Initializing virtual environment with python...
        python -m venv .venv
        if exist ".venv\Scripts\python.exe" (
            set "PY_EXE=.venv\Scripts\python.exe"
            echo [*] Installing dependencies from requirements.txt...
            .venv\Scripts\python.exe -m pip install -r requirements.txt
        ) else (
            set "PY_EXE=python"
        )
    )
)

if "%PY_EXE%"=="" (
    echo.
    echo [X] Error: Python was not found on your system!
    echo     Please install Python 3.10+ and add it to PATH.
    echo.
    pause
    exit /b 1
)

:: 3. Launch application server
echo [*] Launching application server using %PY_EXE%...
echo.

%PY_EXE% -m backend.main

if %errorlevel% neq 0 (
    echo.
    echo [!] Server process exited with code %errorlevel%.
    echo.
    pause
)
