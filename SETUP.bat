@echo off
title Invoice Generator - Setup
color 0F
cls

echo.
echo   ================================================
echo          INVOICE GENERATOR - FIRST TIME SETUP
echo   ================================================
echo.

cd /d "%~dp0"

:: Check Python
echo   Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Python not found.
    echo   Download from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo   Python found.

:: Install fpdf2
echo   Installing required package...
pip install fpdf2 --quiet
echo   Done.

:: Create .env if it doesn't exist
if not exist ".env" (
    echo.
    echo   Creating .env from template...
    copy .env.example .env >nul
    echo   Created .env file.
    echo.
    echo   ================================================
    echo   IMPORTANT: Edit the .env file with your data
    echo   before generating invoices.
    echo   ================================================
    echo.
    echo   Opening .env for editing...
    notepad .env
) else (
    echo.
    echo   .env already exists - skipping.
)

echo.
echo   ================================================
echo   Setup complete. You can now double-click
echo   GENERATE_INVOICE.bat to create invoices.
echo   ================================================
echo.
echo   Press any key to exit...
pause >nul
