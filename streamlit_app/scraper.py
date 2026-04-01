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
        # options.add_argument('--headless') # Uncomment this before deploying to Render!
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-logging"])  
        driver = webdriver.Edge(options=options)
    except:
        try:
            # Fallback to Chrome
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless') # Uncomment this before deploying to Render!
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu') # necessary for headless servers
            options.add_argument('--window-size=1920,1080')
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            # Use Selenium Manager (Selenium 4.10+) which will try to find Chrome in PATH 
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print("[!] Could not start Edge or Chrome. Make sure you have one installed.")
            print("Error details:", str(e))
            return

    wait = WebDriverWait(driver, 10)
    
    # Max attempts to retry captcha
    max_attempts = 8
    
    for attempt in range(max_attempts):
        try:
            print(f"\n[Attempt {attempt + 1}/{max_attempts}]")
            print(f"🌐 Navigating to BISE Lahore results page...")
            
            # Navigate to results page
            driver.get("https://www.biselalhr.edu.pk/SearchResult")
            time.sleep(2)
            
            # Wait for and fill roll number
            print(f"📝 Filling roll number: {roll_no}")
            roll_input = wait.until(EC.presence_of_element_located((By.NAME, 'RollNo')))
            roll_input.clear()
            roll_input.send_keys(roll_no)
            
            # Select Course
            print(f"📚 Selecting course: {course}")
            course_dropdown = Select(driver.find_element(By.NAME, 'Class'))
            course_dropdown.select_by_value(course)
            
            # Select Exam Type
            print(f"🎯 Selecting exam type: {exam_type}")
            exam_dropdown = Select(driver.find_element(By.NAME, 'ExamType'))
            exam_dropdown.select_by_value(exam_type)
            
            # Select Year
            print(f"📅 Selecting year: {year}")
            year_dropdown = Select(driver.find_element(By.NAME, 'Year'))
            year_dropdown.select_by_value(year)
            
            # Handle CAPTCHA
            print("🤖 Detecting and solving CAPTCHA...")
            captcha_img = wait.until(EC.presence_of_element_located((By.ID, 'CaptchaImage')))
            
            # Save captcha image
            captcha_img.screenshot('captcha.png')
            
            # Read and solve captcha using AI
            with open('captcha.png', 'rb') as f:
                captcha_result = ocr.classification(f.read())
                print(f"✅ CAPTCHA solved: {captcha_result}")
            
            # Fill captcha answer
            captcha_input = driver.find_element(By.ID, 'CaptchaText')
            captcha_input.clear()
            captcha_input.send_keys(captcha_result)
            
            # Submit form
            print("🚀 Submitting search form...")
            search_button = driver.find_element(By.ID, 'btnSearch')
            search_button.click()
            
            # Wait for results
            time.sleep(3)
            
            # Check if we got a result
            try:
                error_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'Invalid Roll No')]")
                print("❌ Invalid roll number returned. Retrying with fresh CAPTCHA...")
                continue
            except:
                pass  # No error found, continue to extract data
            
            # Extract student information
            try:
                result_data = {}
                
                # Get name
                name_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Student Name')]/following-sibling::td")
                result_data['Name'] = name_elem.text.strip()
                
                # Get father name
                father_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Father Name')]/following-sibling::td")
                result_data['Father_Name'] = father_elem.text.strip()
                
                # Get roll number
                result_data['Roll_Number'] = roll_no
                
                # Get total marks (with status like PASS/FAIL)
                marks_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Total Marks')]/following-sibling::td")
                result_data['Total_Marks'] = marks_elem.text.strip()
                
                print(f"\n✅ SUCCESS! Data extracted for {result_data['Name']}")
                print(f"   Roll: {result_data['Roll_Number']}")
                print(f"   Marks: {result_data['Total_Marks']}")
                
                driver.quit()
                return result_data
                
            except Exception as e:
                print(f"⚠️ Could not extract data: {str(e)}")
                print("Retrying with new CAPTCHA...")
                continue
        
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_attempts - 1:
                print("🔄 Retrying...")
            continue
    
    print("❌ Failed after all attempts")
    driver.quit()
    return None


if __name__ == "__main__":
    # Test with a roll number
    result = scrape_bise_lahore_selenium("503097")
    if result:
        print("\n" + "="*50)
        print("SCRAPED DATA:")
        print("="*50)
        for key, value in result.items():
            print(f"{key}: {value}")
