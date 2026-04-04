import time
import io
from PIL import Image
import ddddocr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

shared_driver = None
shared_ocr = None

def close_browser():
    global shared_driver
    if shared_driver:
        try:
            shared_driver.quit()
        except:
            pass
        shared_driver = None

def scrape_bise_lahore_selenium(roll_no, course='HSSC', exam_type='2', year='2024'):
    global shared_driver, shared_ocr
    print("\n" + "="*50)
    print("🚀 Starting Visual Browser Automation...")
    print("="*50)
    
    if shared_ocr is None:
        print("Loading ddddocr AI model...")
        shared_ocr = ddddocr.DdddOcr(show_ad=False)
    ocr = shared_ocr

    if shared_driver is None:
        print("Starting Background Application Browser...")
        try:
            # Try to run Edge headless
            options = webdriver.EdgeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_experimental_option("excludeSwitches", ["enable-logging"])  
            shared_driver = webdriver.Edge(options=options)
        except:
            try:
                # Try to run Chrome headless
                options = webdriver.ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu') 
                options.add_argument('--window-size=1920,1080')
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                shared_driver = webdriver.Chrome(options=options)
            except Exception as e:
                print("[!] Could not start Edge or Chrome. Make sure you have one installed.")
                print("Error details:", str(e))
                return False

    driver = shared_driver

    wait = WebDriverWait(driver, 10)
    
    # Max attempts to retry captcha
    max_attempts = 8
    
    for attempt in range(max_attempts):
        print(f"\n--- Attempt {attempt + 1} of {max_attempts} ---")
        driver.get("https://result.biselahore.com/")
        
        try:
            # 1. Wait for Captcha image to appear on screen
            print("Waiting for page and Captcha to load...")
            captcha_img_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'Captcha.aspx')]")))
            
            # 2. Take a screenshot of the Captcha element right off the browser
            # ddddocr is a neural network and handles raw images very well, so we don't need to grayscale it.
            image_bytes = captcha_img_elem.screenshot_as_png
            
            print("Solving Captcha automatically with ddddocr AI...")
            try:
                # Ask ddddocr to classify the raw PNG image bytes
                captcha_text = ocr.classification(image_bytes)
                
                # Clean up the extracted text and force it to be uppercase just in case
                captcha_text = captcha_text.replace(" ", "").replace("\n", "").strip().upper()
                
                # We know captchas are generally exactly 6 characters
                if len(captcha_text) > 6:
                    captcha_text = captcha_text[:6]
                
                print("\n" + "="*60)
                print(f"  [BOT GUESS] >>> The Captcha is: {captcha_text} <<<")
                print("="*60 + "\n")
                
                if len(captcha_text) != 6:
                    print(f"Warning: The bot only read {len(captcha_text)} characters instead of the expected 6. We will let it try anyway.")
                    
            except Exception as e:
                print("\n[WARNING] Failed to solve captcha using ddddocr.")
                print(e)
                # driver.quit()
                return False

            # 3. Fill out the form automatically in the browser
            print("Filling out form fields...")
            
            # Course Radio Button ('rdlistCourse')
            try:
                # The website hides the actual radio dot using opacity: 0 to style it as a custom checkmark.
                # Selenium's standard .click() fails on invisible inputs, so we enforce it using Javascript!
                course_elem = driver.find_element(By.XPATH, f"//input[@name='rdlistCourse' and @value='{course}']")
                driver.execute_script("arguments[0].click();", course_elem)
            except Exception as e:
                print(f"Warning: Could not select Course. Error: {e}")
                
            # Roll Number
            roll_input = driver.find_element(By.ID, "txtFormNo")
            roll_input.clear()
            roll_input.send_keys(str(roll_no))
            
            # Exam Type Dropdown
            Select(driver.find_element(By.ID, "ddlExamType")).select_by_value(exam_type)
            
            # Exam Year Dropdown
            Select(driver.find_element(By.ID, "ddlExamYear")).select_by_value(str(year))
            
            # Captcha Input
            captcha_input = driver.find_element(By.ID, "txtCaptcha")
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)
            
            print("Form filled! Pausing for 5 seconds so you can see exactly what the bot typed before it submits...")
            time.sleep(5) # Give the user time to visibly read the screen
            driver.find_element(By.ID, "Button1").click()
            
            # 4. Check results or errors
            time.sleep(2) # Give the page a moment to respond
            
            try:
                # Check if error label appears with text
                error_label = driver.find_element(By.ID, "lblError")
                error_text = error_label.text.strip()
                if error_text:
                    print("Website returned an error:", error_text)
                    if "Roll No" in error_text:
                        print("Stopping: Invalid Roll Number.")
                        # driver.quit()
                        return False
                    else:
                        print("The ddddocr AI incorrectly guessed the Captcha. Refreshing and retrying...")
                        continue # loop to next attempt
            except:
                pass # No error label exists or is empty, so we probably succeeded!
                
            # Check for Success (Result Displayed)
            try:
                name_elem = driver.find_element(By.ID, "Name")
                name = name_elem.text.strip()
                
                # Father's name ID is usually lblFatherName
                try:
                    father_name = driver.find_element(By.ID, "lblFatherName").text.strip()
                except:
                    father_name = "N/A"
                    
                # Extract Total Marks securely from the final row of the Marks Grid
                total_marks = "0"
                status = "FAIL"
                subject_pass = "FAIL/SUPPLY"
                try:
                    # Finds the table, gets all rows, selects last row, selects last column
                    marks_table = driver.find_element(By.ID, "GridStudentData") 
                    all_rows = marks_table.find_elements(By.TAG_NAME, "tr")
                    
                    # Extract header indices
                    header_cells = all_rows[0].find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = all_rows[0].find_elements(By.TAG_NAME, "td")
                    
                    subject_idx = -1
                    status_idx = -1
                    for i, th in enumerate(header_cells):
                        th_text = th.text.strip().upper()
                        if "NAME OF SUBJECT" in th_text:
                            subject_idx = i
                        elif "RESULT STATUS" in th_text or "STATUS" in th_text:
                            status_idx = i
                            
                    subject_results = []
                    
                    # Parse subject rows
                    if subject_idx != -1 and status_idx != -1:
                        # Iterate through rows, skipping header and last row (totals)
                        for row in all_rows[1:-1]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) > max(subject_idx, status_idx):
                                subj_name = cells[subject_idx].text.strip()
                                subj_status = cells[status_idx].text.strip().upper()
                                # Consider 'LESS THAN 33%' as FAIL
                                if "LESS THAN" in subj_status or subj_status == "FAIL":
                                    subj_status = "FAIL"
                                elif "PASS" in subj_status:
                                    subj_status = "PASS"
                                subject_results.append(f"{subj_name}:{subj_status}")
                                
                    last_row = all_rows[-1] 
                    last_cell = last_row.find_elements(By.TAG_NAME, "td")[-1]   
                    raw_text = last_cell.text.strip().upper()
                    
                    import re
                    if raw_text.isdigit():
                        status = "PASS"
                        subject_pass = ", ".join(subject_results) if subject_results else "All Pass"
                        total_marks = raw_text
                    elif "PASS" in raw_text:
                        numbers = re.findall(r'\d+', raw_text)
                        status = "PASS"
                        subject_pass = ", ".join(subject_results) if subject_results else "All Pass"
                        total_marks = numbers[0] if numbers else "0"
                    else:
                        status = "FAIL"
                        subject_pass = ", ".join(subject_results) if subject_results else raw_text # Store the subject list as status or absent
                        total_marks = "0"
                except Exception as e:
                    pass

                print(f"\n" + "="*50)
                print(f"🎓 RESULT SUCCESSFULLY EXTRACTED FOR ROLL NO {roll_no}")
                print(f"  NAME:           {name}")
                print(f"  FATHER'S NAME:  {father_name}")
                print(f"  STATUS:         {status}")
                print(f"  SUBJECT PASS:   {subject_pass}")
                print(f"  TOTAL MARKS:    {total_marks}")
                print("="*50)

                # Save exactly what you asked for to an Excel-friendly CSV file!
                import csv
                import os

                csv_filename = "Student_Results.csv"
                file_exists = os.path.isfile(csv_filename)

                with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames) 

                    if not file_exists:
                        writer.writeheader() # Write the columns at the top if file is new

                    writer.writerow({
                        'Roll_Number': roll_no,
                        'Name': name,
                        'Father_Name': father_name,
                        'Total_Marks': total_marks,
                        'Status': status,
                        'Subject_Pass': subject_pass
                    })
                
                print(f"Data saved directly to {csv_filename} instead of downloading HTML!")
                
                print("\nStudent scraped successfully! Closing browser and moving to next...")
                time.sleep(3)
                # driver.quit()
                return True
            except Exception as e:
                print("Could not find result data on the page. Something unexpected happened.")
                # driver.quit()
                return False
                
        except Exception as e:
            print("An error occurred trying to interact with the page:", e)
            print("Retrying...")

    print("\n[!] Exhausted all attempts. The ddddocr AI couldn't guess the Captcha correctly.")
    # driver.quit()
    return False


if __name__ == "__main__":
    print("-" * 50)
    print("BISE Lahore Visual Bot")
    print("-" * 50)
    
    print("\n--- Enter Roll Numbers ---")
    print("You can enter a single number (123456), multiple numbers split by a comma (123456, 123457),")
    print("or a range (123456-123460) to scrape multiple students in a row!")
    roll_input = input("Roll Numbers: ")
    
    roll_numbers_to_check = []
    for part in roll_input.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                roll_numbers_to_check.extend(range(int(start), int(end) + 1))
            except:
                pass
        elif part.isdigit():
            roll_numbers_to_check.append(int(part))
            
    if not roll_numbers_to_check:
        print("No valid roll numbers provided. Exiting.")
        import sys
        sys.exit()

    # Matric / Intermediate
    print("\n--- Select Course ---")
    course_type = input("Enter 'SSC' for Matric, or 'HSSC' for Intermediate (Default is HSSC): ").upper()
    if not course_type or course_type not in ['SSC', 'HSSC']:
        course_type = 'HSSC'
        print("Defaulting to: HSSC (Intermediate)")

    # Exam Year
    print("\n--- Select Year ---")
    exam_year = input("Enter Year (e.g., 2024 or 2025): ")
    if not exam_year:
        exam_year = '2024'
        print("Defaulting to: 2024")
    
    # Exam Type (Part-1, Part-II, Suppy)
    print("\n--- Select Exam Type ---")
    print("0 = Supplementary")
    print("1 = Part-I (Annual)")
    print("2 = Part-II (Annual)")
    exam_type_input = input("Enter Exam Type (0, 1, or 2): ")
    if not exam_type_input or exam_type_input not in ['0', '1', '2']:
        exam_type_input = '2'
        print("Defaulting to: 2 (Part-II Annual)")
    
    print(f"\n[!] Preparing to scrape {len(roll_numbers_to_check)} roll numbers in sequence...")
    success_count = 0
    for index, roll in enumerate(roll_numbers_to_check):
        print(f"\n{'#'*60}")
        print(f"# Processing Student {index + 1} of {len(roll_numbers_to_check)} (Roll No: {roll})")
        print(f"{'#'*60}")
        success = scrape_bise_lahore_selenium(
            roll_no=str(roll),
            course=course_type,
            exam_type=exam_type_input,
            year=exam_year
        )
        if success:
            success_count += 1
    
    print("\n" + "="*50)
    print(f"🎉 Scraping Complete!")
    print(f"Successfully processed {success_count} out of {len(roll_numbers_to_check)} roll numbers.")
    print("="*50)
    print("Check Student_Results.csv for the data!")
    close_browser()
