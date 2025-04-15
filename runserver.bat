@echo off
cd /d %USERPROFILE%\Documents\log2
echo Activating virtual environment...
call venv\Scripts\activate
echo Starting Django server...
cd /d %USERPROFILE%\Documents\log2\tre-logistica-2
python manage.py runserver
pause
