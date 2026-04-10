# Student Results Platform - Detailed Guide

This document explains the project in simple words so a new coder can understand and maintain it.

## 1) What this project does

- Shows student results in a clean web UI
- Lets you upload CSV/Excel files
- Builds graphs and statistics
- Generates a PDF report
- Scrapes BISE Lahore results using fast HTTP requests (no Selenium)

## 2) How the system works (big picture)

1. You open the web app.
2. The app loads data from Student_Results.csv.
3. Graphs are created in the browser with Chart.js.
4. The scraper can fetch results in the background and save to CSV.
5. A PDF report is generated from the CSV when you click download.

## 3) Project structure

```
Result_fatch/
├── app.py                # Flask app and API endpoints
├── scraper.py            # Requests-based scraper
├── generate_report.py    # PDF report generator
├── Student_Results.csv   # Data file
├── templates/            # HTML templates
├── static/               # CSS and JS
└── requirements.txt      # Python dependencies
```

## 4) How the scraper works

The scraper does not open a browser. It does this instead:

1. Sends a GET request to the result page.
2. Reads hidden form fields (like __VIEWSTATE).
3. Downloads the captcha image and solves it using OCR.
4. Sends a POST request with roll number + captcha.
5. Parses the HTML response to extract the result.
6. Saves the data to Student_Results.csv.

### Safety features

- Random delay between requests (2 to 5 seconds)
- Retry on failures and captcha errors
- Browser-like request headers
- Connection pooling for speed

## 5) Scraper functions (simple explanation)

- `load_roll_numbers()`
  - Reads input like `123, 124-130` and returns a list of numbers.

- `send_request()`
  - Sends the POST request that returns the result page.

- `parse_result_page()`
  - Reads the HTML and extracts name, marks, status, subjects.

- `process_roll_number()`
  - Runs all steps for one roll number with retries.

- `save_results()`
  - Appends results to Student_Results.csv.

- `scrape_roll_numbers_parallel()`
  - Runs many roll numbers at the same time using threads.

## 6) Run the project

### Setup

```bash
# Activate venv (example for Windows Git Bash)
source scrap_web/Scripts/activate

# Install dependencies
pip install -r requirements.txt
```

### Run web app

```bash
python app.py
```

Open:

```
http://127.0.0.1:5000
```

### Run scraper (CLI)

```bash
python scraper.py
```

## 7) Scraper speed settings

- Default parallel workers: 10
- You can change it using an environment variable:

```bash
# Windows CMD
set SCRAPER_MAX_WORKERS=10

# PowerShell
$env:SCRAPER_MAX_WORKERS="10"
```

## 8) Render deployment (recommended)

Render web services should stay responsive, so run scraping in a worker.

1. Create a Redis instance on Render.
2. Set `REDIS_URL` in both the web and worker services.
3. Start commands:

```bash
# Web service
python app.py

# Worker service
python worker.py
```

## 8) CSV format

Required columns:

```
Roll_Number,Name,Father_Name,Total_Marks
```

Optional columns (added by scraper):

```
Status,Subject_Pass
```

## 9) Graphs and PDF

- Graphs use `/api/results` and are updated on the client side.
- PDF reads the CSV and builds charts using Matplotlib and ReportLab.
- If a subject column does not exist, PDF uses `Subject_Pass` to build subject charts.

## 10) Error handling

- Invalid roll numbers are detected and logged.
- Failed roll numbers are saved to `failed_rolls.txt`.
- Captcha failures are retried automatically.

## 11) Troubleshooting

- If PDF fails, make sure `reportlab` and `matplotlib` are installed.
- If graphs are wrong, check values in Student_Results.csv.
- Captcha OCR can fail. Retry is built in.

## 12) Contributing tips

- Keep functions small and clear.
- Avoid changing CSV column names.
- Test with a small list before scraping thousands.

## 13) Useful commands

```bash
python app.py
python scraper.py
pip install -r requirements.txt
```
