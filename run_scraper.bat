@echo off
echo Activating virtual environment 'scrap_web'...
call scrap_web\Scripts\activate.bat
python scraper.py
pause
