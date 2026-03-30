@echo off
echo Creating Python virtual environment 'scrap_web'...
python -m venv scrap_web
echo Activating virtual environment...
call scrap_web\Scripts\activate.bat
echo Installing required Python libraries for the BISE Lahore Scraper...
pip install requests beautifulsoup4 pillow ddddocr selenium
echo.
echo Installation complete! You can now run the scraper by double-clicking 'run_scraper.bat'
pause
