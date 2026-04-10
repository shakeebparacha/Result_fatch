from flask import Flask, request, jsonify, render_template, send_file
from scraper import load_roll_numbers, scrape_roll_numbers_parallel
import threading
import csv
import os
import io
try:
    import pandas as pd
except ImportError as e:
    print(f"Warning: Pandas could not be imported ({e}). Excel upload will be disabled.")
    pd = None
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = Flask(__name__, template_folder='templates')

# Ensure Student_Results.csv is in the correct location
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Student_Results.csv')

# ================== PDF GENERATION FUNCTIONS ==================

def calculate_statistics():
    """Calculate overall statistics from CSV data"""
    stats = {
        'total_students': 0,
        'pass_count': 0,
        'fail_count': 0,
        'subjects': {}  # subject -> {total, pass, fail}
    }
    
    if not os.path.exists(CSV_FILE):
        return stats
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # ignore completely empty rows or rows without roll numbers
                if not any(str(v).strip() for v in row.values()) or not row.get('Roll_Number') or not str(row.get('Roll_Number')).strip():
                    continue
                    
                stats['total_students'] += 1
                status = row.get('Status', '').upper()
                
                if 'PASS' in status:
                    stats['pass_count'] += 1
                else:
                    stats['fail_count'] += 1
                
                # Parse subject information if available
                subject_info = row.get('Subject_Pass', '')
                if subject_info and 'PASS' not in status:
                    subjects_list = [s.strip() for s in subject_info.split(',')]
                    for subject in subjects_list:
                        if subject not in stats['subjects']:
                            stats['subjects'][subject] = {'total': 0, 'pass': 0, 'fail': 0}
                        stats['subjects'][subject]['total'] += 1
                        stats['subjects'][subject]['fail'] += 1
    except Exception as e:
        print(f"Error calculating statistics: {e}")
    
    return stats

def generate_pdf_report():
    """Generate a professional PDF report with statistics"""
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4338ca'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Title
    title = Paragraph("BISE LAHORE EXAMINATION RESULTS REPORT", title_style)
    story.append(title)
    
    # Generated date
    date_text = Paragraph(f"<i>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", normal_style)
    story.append(date_text)
    story.append(Spacer(1, 0.3*inch))
    
    # Get statistics
    stats = calculate_statistics()
    
    # ===== OVERALL STATISTICS TABLE =====
    story.append(Paragraph("OVERALL STATISTICS", heading_style))
    
    total = stats['total_students']
    pass_count = stats['pass_count']
    fail_count = stats['fail_count']
    
    # Calculate percentages
    pass_pct = (pass_count / total * 100) if total > 0 else 0
    fail_pct = (fail_count / total * 100) if total > 0 else 0
    
    overall_data = [
        ['Metric', 'Count', 'Percentage'],
        ['Total Students', str(total), f'{100:.1f}%'],
        ['Passed', str(pass_count), f'{pass_pct:.1f}%'],
        ['Failed/Supply', str(fail_count), f'{fail_pct:.1f}%'],
    ]
    
    overall_table = Table(overall_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    overall_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    
    story.append(overall_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== SUBJECT-WISE DETAILS TABLE =====
    if stats['subjects']:
        story.append(PageBreak())
        story.append(Paragraph("SUBJECT-WISE ANALYSIS", heading_style))
        
        subject_data = [
            ['Subject', 'Total Students', 'Passed', 'Failed/Supply', 'Pass Rate'],
        ]
        
        for subject, counts in sorted(stats['subjects'].items()):
            total_sub = counts['total']
            pass_sub = counts['total'] - counts['fail']
            fail_sub = counts['fail']
            pass_rate = (pass_sub / total_sub * 100) if total_sub > 0 else 0
            
            subject_data.append([
                subject,
                str(total_sub),
                str(pass_sub),
                str(fail_sub),
                f'{pass_rate:.1f}%'
            ])
        
        subject_table = Table(subject_data, colWidths=[2*inch, 1.3*inch, 1*inch, 1.2*inch, 1.2*inch])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        
        story.append(subject_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Footer note
    footer = Paragraph(
        "<i>This report is auto-generated from the BISE Lahore Examination Result Scraper. All data is confidential.</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

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
    "messagde": ""
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

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# ================== API ENDPOINTS ==================

@app.route('/api/results', methods=['GET'])
def get_results():
    """Fetch all results from CSV"""
    try:
        results_list = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Ignore rows where 'Roll_Number' or 'Name' is completely empty or just spaces.
                # Adjust depending on which columns must be filled for a row to be valid.
                results_list = [
                    row for row in reader 
                    if any(str(v).strip() for v in row.values())
                    and row.get('Roll_Number') 
                    and str(row.get('Roll_Number')).strip()
                ]
        
        response = jsonify({"status": "success", "data": results_list})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
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
            if pd is None:
                 return jsonify({"status": "error", "message": "Excel files are not supported in your environment. Please upload a CSV instead."}), 400
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

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear all data from the CSV file keep headers"""
    try:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass'])
            
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
        return jsonify({"status": "success", "message": "Data cleared successfully"})
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
                results_list = [
                    row for row in reader 
                    if any(str(v).strip() for v in row.values())
                    and row.get('Roll_Number') 
                    and str(row.get('Roll_Number')).strip()
                ]
        
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
    roll_list = load_roll_numbers(roll_numbers)

    total = len(roll_list)
    scraping_status["is_running"] = True
    scraping_status["total"] = total
    scraping_status["processed"] = 0
    scraping_status["success"] = 0
    scraping_status["message"] = f"Initializing scraper for {total} roll numbers..."

    print(f"[!] Background worker starting! Processing {total} target(s)...")

    def progress_callback(roll_no, result):
        scraping_status["processed"] += 1
        if result.get("success") == "True":
            scraping_status["success"] += 1
        scraping_status["message"] = (
            f"Completed {scraping_status['processed']} of {total} roll numbers. "
            f"Last roll: {roll_no}"
        )

    summary = scrape_roll_numbers_parallel(
        roll_numbers=roll_list,
        course=course,
        exam_type=exam_type_val,
        year=exam_year,
        max_workers=int(os.getenv("SCRAPER_MAX_WORKERS", "10")),
        csv_file=CSV_FILE,
        progress_callback=progress_callback,
        use_tqdm=False,
    )

    scraping_status["message"] = (
        f"Finished! Successfully scraped {summary['success']} out of {total} roll numbers."
    )
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

@app.route('/api/download-pdf', methods=['GET', 'POST'])
def download_pdf():
    """Generate and download PDF report"""
    try:
        import generate_report
        import importlib
        importlib.reload(generate_report)
        institute_name = request.args.get('institute_name', 'INSTITUTE OF EXCELLENCE')
        
        import uuid
        pdf_id = uuid.uuid4().hex
        
        pdf_csv_path = CSV_FILE
        temp_csv = None
        if request.method == 'POST' and request.is_json:
            data = request.json
            if data and len(data) > 0:
                import pandas as pd
                temp_csv = f"temp_data_{pdf_id}.csv"
                pd.DataFrame(data).to_csv(temp_csv, index=False)
                pdf_csv_path = temp_csv

        pdf_filename = f"Academic_Performance_Report_{pdf_id}.pdf"
        generate_report.generate_report(csv_file=pdf_csv_path, output_pdf=pdf_filename, institute_name=institute_name)
        
        response = send_file(
            os.path.abspath(pdf_filename),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Cleanup
        if temp_csv and os.path.exists(temp_csv):
            try: os.remove(temp_csv)
            except: pass
            
        return response
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
    app.run(port=5000, debug=True, use_reloader=False)
