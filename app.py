from flask import Flask, request, jsonify, render_template, Response
from scraper import scrape_bise_lahore_selenium
import threading
import sys
import os

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

def background_scraper(roll_numbers, course, exam_year, exam_type_val):
    # Parse roll numbers exactly like your CLI did
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
    # Loop over the results in the background
    for roll in roll_list:
        scrape_bise_lahore_selenium(
            roll_no=str(roll), 
            course=course, 
            exam_type=exam_type_val, 
            year=exam_year
        )
    print("\n[!] Background worker finished completely.")

@app.route('/scrape', methods=['POST'])
def start_scraping():
    data = request.json
    roll_numbers = data.get('rollNumbers', '')
    course = data.get('courseType', 'HSSC')
    exam_year = data.get('examYear', '2024')
    exam_type_val = data.get('examTypeVal', '2')
    
    # Run the selenium tasks in a background thread so the browser doesn't freeze waiting
    thread = threading.Thread(target=background_scraper, args=(roll_numbers, course, exam_year, exam_type_val))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "success", "message": "Bot is starting! Check the terminal for progress in the meantime..."})

if __name__ == '__main__':
    print("🚀 App UI is running at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop.")
    app.run(port=5000, debug=True)

