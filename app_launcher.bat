@echo off
echo Starting BISE Lahore Web Application...
call scrap_web\Scripts\activate.bat
start http://127.0.0.1:5000
python app.py
pause