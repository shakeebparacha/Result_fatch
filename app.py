from flask import Flask, request, jsonify, render_template, send_file
from scraper import scrape_bise_lahore_selenium
import threading
import csv
import os
import io
import pandas as pd
from datetime import datetime

app = Flask(__name__, template_folder='templates')

# Ensure Student_Results.csv is in the correct location
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Student_Results.csv')

# ================== INITIALIZATION ==================
def initialize_csv():
    """Clear CSV file on app startup with headers only"""
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass'])
            writer.writeheader()
        print(f"✓ CSV initialized (cleared on startup): {CSV_FILE}")
    except Exception as e:
        print(f"✗ Error initializing CSV: {e}")

# Initialize CSV on app startup
initialize_csv()

# ================== ROUTES ==================

# Global dictionary to track scraping progress
scraping_status = {
    "is_running": False,
    "total": 0,
    "processed": 0,
    "success": 0,
    "message": ""
}

@app.route('/')
def home():
    """Home page"""
    return render_template('home.html')

@app.route('/results')
def results():
    """Results page with table and upload"""
    return render_template('results.html')

@app.route('/graphs')
def graphs():
    """Graphs and data visualization page"""
    return render_template('graphs.html')

@app.route('/scraper')
def scraper():
    """Scraper automation page"""
    return render_template('scraper.html')

# ================== API ENDPOINTS ==================

@app.route('/api/results', methods=['GET'])
def get_results():
    """Fetch all results from CSV"""
    try:
        results_list = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                results_list = list(reader)
        return jsonify({"status": "success", "data": results_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Upload and overwrite CSV or Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        ext = file.filename.lower().split('.')[-1]
        if ext not in ['csv', 'xlsx', 'xls']:
            return jsonify({"status": "error", "message": "Only CSV and Excel files (.xls/.xlsx) are allowed"}), 400

        # Read and validate File
        if ext == 'csv':
            stream = io.TextIOWrapper(file.stream, encoding='utf-8')
            reader = csv.DictReader(stream)
            fieldnames = reader.fieldnames
            rows = list(reader)
        else:
            # Excel handler
            df = pd.read_excel(file.stream)
            df = df.fillna('') # Handle empty cells
            fieldnames = list(df.columns)
            rows = df.to_dict('records')

        if not rows:
            return jsonify({"status": "error", "message": "File is empty"}), 400

        # Check for required column
        if 'Roll_Number' not in fieldnames:
            return jsonify({"status": "error", "message": "File must contain 'Roll_Number' column"}), 400

        # Overwrite CSV file
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return jsonify({
            "status": "success",
            "message": f"Successfully uploaded {len(rows)} records",
            "count": len(rows)
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/download-sample', methods=['GET'])
def download_sample():
    """Download sample CSV template"""
    try:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass'])
        writer.writeheader()
        writer.writerow({
            'Roll_Number': '123456',
            'Name': 'STUDENT NAME',
            'Father_Name': 'FATHER NAME',
            'Total_Marks': '449',
            'Status': 'PASS',
            'Subject_Pass': 'All Pass'
        })
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='Sample_Roll_Numbers.csv'
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/graph-data', methods=['GET'])
def get_graph_data():
    """Fetch data for graphs"""
    try:
        results_list = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                results_list = list(reader)
        
        # Process data for graphs
        pass_count = 0
        fail_count = 0

        for row in results_list:
            status_str = row.get('Status', '').lower()
            if not status_str and 'Total_Marks' in row:
                status_str = row['Total_Marks'].lower()
                
            if 'pass' in status_str:
                pass_count += 1
            elif status_str: # only count fail if status isn't totally empty
                fail_count += 1

        return jsonify({
            "status": "success",
            "total_students": len(results_list),
            "pass_count": pass_count,
            "fail_count": fail_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ================== SCRAPER ENDPOINT ==================

def background_scraper(roll_numbers, course, exam_year, exam_type_val):
    """Background scraper worker"""
    global scraping_status
    roll_list = []
    for part in roll_numbers.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                roll_list.extend(range(int(start), int(end) + 1))
            except: pass
        elif part.isdigit():
            roll_list.append(int(part))

    total = len(roll_list)
    scraping_status["is_running"] = True
    scraping_status["total"] = total
    scraping_status["processed"] = 0
    scraping_status["success"] = 0
    scraping_status["message"] = f"Initializing scraper for {total} roll numbers..."

    print(f"[!] Background worker starting! Processing {total} target(s)...")
    for roll in roll_list:
        scraping_status["message"] = f"Processing Roll No: {roll} ({scraping_status['processed'] + 1}/{total})"
        is_success = scrape_bise_lahore_selenium(
            roll_no=str(roll),
            course=course,
            exam_type=exam_type_val,
            year=exam_year
        )
        if is_success:
            scraping_status["success"] += 1
        scraping_status["processed"] += 1

    scraping_status["message"] = f"Finished! Successfully scraped {scraping_status['success']} out of {total} roll numbers."
    scraping_status["is_running"] = False
    print("\n[!] Background worker finished completely.")

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """Start background scraping task"""
    global scraping_status
    if scraping_status["is_running"]:
        return jsonify({"status": "error", "message": "A scraping task is already running."}), 400
    try:
        data = request.json
        roll_numbers = data.get('rollNumbers', '')
        course = data.get('courseType', 'HSSC')
        exam_year = data.get('examYear', '2024')
        exam_type_val = data.get('examTypeVal', '2')
        
        thread = threading.Thread(target=background_scraper, args=(roll_numbers, course, exam_year, exam_type_val))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": "Bot is starting! Check the tracking log below..."
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/scrape-status', methods=['GET'])
def scrape_status():
    """Get the current progress of the scraper"""
    global scraping_status
    return jsonify(scraping_status)

# ================== ERROR HANDLERS ==================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 Student Results Platform running at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop.")
    app.run(port=5000, debug=True)

