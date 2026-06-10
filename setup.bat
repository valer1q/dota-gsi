@echo off
REM Создаёт виртуальное окружение .venv и ставит в него flask.
REM Запускать из папки проекта двойным кликом или: setup.bat

cd /d "%~dp0"

echo [1/3] Создаю виртуальное окружение .venv ...
python -m venv .venv
if errorlevel 1 (
    echo.
    echo ОШИБКА: не удалось создать venv. Проверь, что Python установлен:
    echo     python --version
    echo Если команды нет - поставь Python с python.org с галкой "Add to PATH".
    pause
    exit /b 1
)

echo [2/3] Обновляю pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo [3/3] Ставлю flask ...
".venv\Scripts\python.exe" -m pip install flask
if errorlevel 1 (
    echo ОШИБКА: не удалось поставить flask.
    pause
    exit /b 1
)

echo.
echo Готово. Окружение .venv создано, flask установлен.
echo Теперь запускай сервер через run.bat
echo.
pause
