@echo off
title Invoice Generator
color 0F
cls

echo.
echo   ================================================
echo          MONTHLY INVOICE GENERATOR
echo   ================================================
echo.
echo   Double-click to generate your monthly invoice.
echo   Just answer the prompts below.
echo.
echo   ------------------------------------------------
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found!
    echo   Install Python 3.10+ and add it to PATH.
    echo.
    pause
    exit /b 1
)

:: Check .env exists
if not exist ".env" (
    echo   [ERROR] .env file not found!
    echo   Copy .env.example to .env and fill in your data.
    echo.
    pause
    exit /b 1
)

:: Check fpdf2
python -c "import fpdf" >nul 2>&1
if errorlevel 1 (
    echo   Installing required package fpdf2...
    pip install fpdf2 --quiet
    echo   Done.
    echo.
)

:: Run the invoice generator
python generate_monthly_invoice.py

echo.
echo   ------------------------------------------------
echo   Press any key to exit...
pause >nul
