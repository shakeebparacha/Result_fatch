from flask import Flask, request, jsonify, render_template, send_file
from scraper import scrape_bise_lahore_selenium
import threading
import csv
import os
import io
from datetime import datetime

app = Flask(__name__, template_folder='templates')

CSV_FILE = 'Student_Results.csv'

# ================== ROUTES ==================

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
    """Upload and overwrite CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"status": "error", "message": "Only CSV files are allowed"}), 400
        
        # Read and validate CSV
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        rows = list(reader)
        
        if not rows:
            return jsonify({"status": "error", "message": "CSV file is empty"}), 400
        
        # Check for required column
        if 'Roll_Number' not in reader.fieldnames:
            return jsonify({"status": "error", "message": "CSV must contain 'Roll_Number' column"}), 400
        
        # Overwrite CSV file
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = reader.fieldnames
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
        writer = csv.DictWriter(output, fieldnames=['Roll_Number', 'Name', 'Father_Name', 'Total_Marks'])
        writer.writeheader()
        writer.writerow({
            'Roll_Number': '123456',
            'Name': 'STUDENT NAME',
            'Father_Name': 'FATHER NAME',
            'Total_Marks': 'PASS XXX or SUBJECT LIST'
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
            if 'Total_Marks' in row:
                marks_str = row['Total_Marks'].lower()
                if 'pass' in marks_str:
                    pass_count += 1
                else:
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
            
    print(f"[!] Background worker starting! Processing {len(roll_list)} target(s)...")
    for roll in roll_list:
        scrape_bise_lahore_selenium(
            roll_no=str(roll), 
            course=course, 
            exam_type=exam_type_val, 
            year=exam_year
        )
    print("\n[!] Background worker finished completely.")

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """Start background scraping task"""
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
            "message": "Bot is starting! Check the terminal for progress..."
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

