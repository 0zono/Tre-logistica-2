@echo off
setlocal enabledelayedexpansion
:: Set project directories
set PROJECT_DIR=%USERPROFILE%\Documents\log2\tre-logistica-2
set VENV_DIR=%USERPROFILE%\Documents\log2\venv

:: Check Python installation
py --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate" || (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Change to project directory
cd /d "%PROJECT_DIR%" || (
    echo Cannot find project directory.
    pause
    exit /b 1
)


:: Run migrations
echo Running database migrations...
py manage.py migrate || (
    echo Migration failed.
    pause
    exit /b 1
)

:: Create superuser if not exists
echo Checking superuser...
py manage.py createsuperuser --username=admin --email=admin@example.com --noinput || (
    echo Superuser setup failed or already exists.
    pause
    exit /b 1
)

:: Start Django development server
echo Starting Django server...
py manage.py runserver