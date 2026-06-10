@echo off
REM Генерирует gamestate_integration_items.cfg для клиента Доты.
REM Двойной клик или: make-config.bat

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Виртуальное окружение не найдено. Сначала запусти setup.bat
    pause
    exit /b 1
)

".venv\Scripts\python.exe" gsi_server.py --make-config

echo.
pause
