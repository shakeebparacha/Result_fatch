import time
import io
from PIL import Image
import ddddocr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

def scrape_bise_lahore_selenium(roll_no, course='HSSC', exam_type='2', year='2024'):
    print("\n" + "="*50)
    print("🚀 Starting Visual Browser Automation...")
    print("="*50)
    
    print("Loading ddddocr AI model...")
    ocr = ddddocr.DdddOcr(show_ad=False)

    try:
        # Try Edge first since it's built into Windows
        options = webdriver.EdgeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Edge(options=options)
    except:
        try:
            # Fallback to Chrome
            options = webdriver.ChromeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print("[!] Could not start Edge or Chrome. Make sure you have one installed.")
            print("Error details:", e)
            return

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
                driver.quit()
                return

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
                        driver.quit()
                        return
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
                total_marks = "N/A"
                try:
                    # Finds the table, gets all rows, selects last row, selects last column
                    marks_table = driver.find_element(By.ID, "GridStudentData")
                    last_row = marks_table.find_elements(By.TAG_NAME, "tr")[-1]
                    last_cell = last_row.find_elements(By.TAG_NAME, "td")[-1]
                    total_marks = last_cell.text.strip() # This extracts exactly "PASS 449"
                except Exception as e:
                    pass
                
                print(f"\n" + "="*50)
                print(f"🎓 RESULT SUCCESSFULLY EXTRACTED FOR ROLL NO {roll_no}")
                print(f"  NAME:           {name}")
                print(f"  FATHER'S NAME:  {father_name}")
                print(f"  TOTAL MARKS:    {total_marks}")
                print("="*50)
                
                # Save exactly what you asked for to an Excel-friendly CSV file!
                import csv
                import os
                
                csv_filename = "Student_Results.csv"
                file_exists = os.path.isfile(csv_filename)
                
                with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    if not file_exists:
                        writer.writeheader() # Write the columns at the top if file is new
                        
                    writer.writerow({
                        'Roll_Number': roll_no,
                        'Name': name,
                        'Father_Name': father_name,
                        'Total_Marks': total_marks
                    })
                
                print(f"Data saved directly to {csv_filename} instead of downloading HTML!")
                
                print("\nStudent scraped successfully! Closing browser and moving to next...")
                time.sleep(3)
                driver.quit()
                return
            except Exception as e:
                print("Could not find result data on the page. Something unexpected happened.")
                driver.quit()
                return
                
        except Exception as e:
            print("An error occurred trying to interact with the page:", e)
            print("Retrying...")

    print("\n[!] Exhausted all attempts. The ddddocr AI couldn't guess the Captcha correctly.")
    driver.quit()


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
    for index, roll in enumerate(roll_numbers_to_check):
        print(f"\n{'#'*60}")
        print(f"# Processing Student {index + 1} of {len(roll_numbers_to_check)} (Roll No: {roll})")
        print(f"{'#'*60}")
        scrape_bise_lahore_selenium(
            roll_no=str(roll),
            course=course_type,
            exam_type=exam_type_input,
            year=exam_year
        )
    
    print("\nAll requested roll numbers have been processed! Check Student_Results.csv!")
