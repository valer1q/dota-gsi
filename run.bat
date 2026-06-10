@echo off
REM Запускает GSI-сервер внутри venv (.venv).
REM Двойной клик или: run.bat              -> поднять сервер
REM             run.bat --make-config       -> сгенерить .cfg и выйти

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Виртуальное окружение не найдено. Сначала запусти setup.bat
    pause
    exit /b 1
)

".venv\Scripts\python.exe" gsi_server.py %*

pause
