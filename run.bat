@echo off
REM Скрипт для запуска AI-Tutor на Windows
REM Явно использует Python 3.13

echo.
echo ========================================
echo  AI-Tutor: Personalized School Navigator
echo ========================================
echo.

REM Проверяем Python 3.13
py -3.13 --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.13 not found!
    echo Please install Python 3.13 from https://python.org
    pause
    exit /b 1
)

echo [INFO] Starting AI-Tutor with Python 3.13...
echo [INFO] This will initialize Ollama and all dependencies on first run
echo.

REM Запускаем main.py с Python 3.13
py -3.13 main.py

pause
