@echo off
title BISE Lahore Project Manager
:MENU
cls
echo ===============================================
echo       BISE Lahore Project Manager
echo ===============================================
echo.
echo 1. Install Requirements (Setup environment)
echo 2. Run Scraper Script Only
echo 3. Start Web Application (Flask)
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto SCRAPER
if "%choice%"=="3" goto WEBAPP
if "%choice%"=="4" goto EOF
goto MENU

:INSTALL
echo.
echo Setting up virtual environment...
python -m venv scrap_web
echo Activating and installing requirements...
call scrap_web\Scripts\activate.bat
pip install -r requirements.txt
echo Setup complete!
pause
goto MENU

:SCRAPER
echo.
echo Running Scraper...
call scrap_web\Scripts\activate.bat
python scraper.py
pause
goto MENU

:WEBAPP
echo.
echo Starting Web Application...
call scrap_web\Scripts\activate.bat
start http://127.0.0.1:5000
python app.py
pause
goto MENU

:EOF
exit
