import csv
import logging
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import ddddocr
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://result.biselahore.com/"
DEFAULT_TIMEOUT = 12
DEFAULT_DELAY_RANGE = (2, 5)
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_MAX_WORKERS = 10
DEFAULT_POOL_MAXSIZE = 50
DEFAULT_FLUSH_EVERY = 25

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
    "Origin": BASE_URL,
    "Connection": "keep-alive",
}

_logger = logging.getLogger("bise_scraper")
_thread_local = threading.local()


def setup_logging(log_path: str = "scraper.log") -> None:
    if _logger.handlers:
        return
    _logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    _logger.addHandler(stream_handler)


def get_ocr() -> ddddocr.DdddOcr:
    if not hasattr(_thread_local, "ocr"):
        _thread_local.ocr = ddddocr.DdddOcr(show_ad=False)
    return _thread_local.ocr


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=DEFAULT_POOL_MAXSIZE,
            pool_maxsize=DEFAULT_POOL_MAXSIZE,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(DEFAULT_HEADERS)
        _thread_local.session = session
    return _thread_local.session


def normalize_delay_range(delay_range: Tuple[int, int]) -> Tuple[int, int]:
    low, high = delay_range
    low = max(0, int(low))
    high = max(low, int(high))
    return low, high


def load_roll_numbers(roll_input: str) -> List[int]:
    roll_numbers: List[int] = []
    invalid_entries: List[str] = []
    duplicate_entries: List[str] = []
    seen: set = set()

    def add_roll(value: int, label: str) -> None:
        if len(str(value)) > 7:
            invalid_entries.append(label)
            return
        if value in seen:
            duplicate_entries.append(label)
            return
        seen.add(value)
        roll_numbers.append(value)

    for part in roll_input.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = part.split("-")
                start = start.strip()
                end = end.strip()
                if not start.isdigit() or not end.isdigit():
                    invalid_entries.append(part)
                    continue
                start_val = int(start)
                end_val = int(end)
                if start_val > end_val:
                    start_val, end_val = end_val, start_val
                for value in range(start_val, end_val + 1):
                    add_roll(value, str(value))
            except ValueError:
                invalid_entries.append(part)
                continue
        elif part.isdigit():
            add_roll(int(part), part)
        else:
            invalid_entries.append(part)

    if duplicate_entries:
        print("Duplicate roll numbers removed:", ", ".join(duplicate_entries))
    if invalid_entries:
        print("Invalid roll numbers removed (non-numeric or >7 digits):", ", ".join(invalid_entries))

    return roll_numbers


def extract_hidden_fields(soup: BeautifulSoup) -> Dict[str, str]:
    hidden_fields: Dict[str, str] = {}
    for input_tag in soup.find_all("input", {"type": "hidden"}):
        name = input_tag.get("name")
        if not name:
            continue
        hidden_fields[name] = input_tag.get("value", "")
    return hidden_fields


def find_captcha_url(soup: BeautifulSoup) -> Optional[str]:
    captcha_img = soup.find("img", src=lambda value: value and "Captcha" in value)
    if not captcha_img:
        return None
    src = captcha_img.get("src", "")
    if not src:
        return None
    return urljoin(BASE_URL, src)


def fetch_form(session: requests.Session) -> BeautifulSoup:
    response = session.get(BASE_URL, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def solve_captcha(session: requests.Session, captcha_url: str) -> str:
    response = session.get(captcha_url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    captcha_text = get_ocr().classification(response.content)
    captcha_text = re.sub(r"\s+", "", captcha_text).upper()
    return captcha_text[:6]


def build_payload(
    roll_no: str,
    course: str,
    exam_type: str,
    year: str,
    captcha_text: str,
    hidden_fields: Dict[str, str],
) -> Dict[str, str]:
    payload = dict(hidden_fields)
    payload.update(
        {
            "txtFormNo": str(roll_no),
            "txtCaptcha": captcha_text,
            "ddlExamType": str(exam_type),
            "ddlExamYear": str(year),
            "rdlistCourse": course,
            "Button1": "View Result",
        }
    )
    return payload


def send_request(session: requests.Session, payload: Dict[str, str]) -> str:
    response = session.post(BASE_URL, data=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_result_page(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    error_label = soup.find(id="lblError")
    if error_label:
        error_text = error_label.get_text(strip=True)
        if error_text:
            return {
                "success": "False",
                "error": error_text,
                "error_type": "captcha" if "captcha" in error_text.lower() else "invalid",
            }

    name_elem = soup.find(id="Name")
    if not name_elem:
        return {
            "success": "False",
            "error": "Result data not found",
            "error_type": "missing",
        }

    name = name_elem.get_text(strip=True)
    father_name_elem = soup.find(id="lblFatherName")
    father_name = father_name_elem.get_text(strip=True) if father_name_elem else "N/A"

    total_marks = "0"
    status = "FAIL"
    subject_pass = "FAIL/SUPPLY"

    table = soup.find(id="GridStudentData")
    subject_results: List[str] = []
    if table:
        rows = table.find_all("tr")
        for row in rows[1:-1]:
            cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
            if not cells:
                continue
            if len(cells) == 6:
                subject_name, subject_mark, subject_status = cells[0], cells[2], cells[5]
            elif len(cells) >= 11:
                subject_name, subject_mark, subject_status = cells[0], cells[5], cells[10]
            else:
                continue

            upper_name = subject_name.upper()
            if "SUBJECT" in upper_name or "MARKS" in upper_name:
                continue

            subject_results.append(f"{subject_name}:{subject_mark}:{subject_status}")

        if rows:
            last_row = rows[-1]
            last_cells = last_row.find_all("td")
            if last_cells:
                raw_text = last_cells[-1].get_text(strip=True).upper()
                if raw_text.isdigit():
                    status = "PASS"
                    total_marks = raw_text
                    subject_pass = ", ".join(subject_results) if subject_results else "All Pass"
                elif "PASS" in raw_text:
                    numbers = re.findall(r"\d+", raw_text)
                    status = "PASS"
                    total_marks = numbers[0] if numbers else "0"
                    subject_pass = ", ".join(subject_results) if subject_results else "All Pass"
                else:
                    status = "FAIL"
                    subject_pass = ", ".join(subject_results) if subject_results else raw_text

    return {
        "success": "True",
        "Name": name,
        "Father_Name": father_name,
        "Total_Marks": total_marks,
        "Status": status,
        "Subject_Pass": subject_pass,
    }


def process_roll_number(
    roll_no: int,
    course: str,
    exam_type: str,
    year: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    delay_range: Tuple[int, int] = DEFAULT_DELAY_RANGE,
) -> Dict[str, str]:
    session = get_session()
    delay_range = normalize_delay_range(delay_range)
    for attempt in range(1, max_attempts + 1):
        time.sleep(random.uniform(*delay_range))
        try:
            soup = fetch_form(session)
            hidden_fields = extract_hidden_fields(soup)
            captcha_url = find_captcha_url(soup)
            if not captcha_url:
                return {
                    "success": "False",
                    "error": "Captcha image not found",
                    "error_type": "missing",
                }

            captcha_text = solve_captcha(session, captcha_url)
            payload = build_payload(
                roll_no=str(roll_no),
                course=course,
                exam_type=exam_type,
                year=year,
                captcha_text=captcha_text,
                hidden_fields=hidden_fields,
            )

            html = send_request(session, payload)
            result = parse_result_page(html)
            if result.get("success") == "True":
                result["Roll_Number"] = str(roll_no)
                return result

            error_type = result.get("error_type")
            if error_type == "captcha" and attempt < max_attempts:
                _logger.info("Captcha failed for roll %s. Retrying...", roll_no)
                continue

            return result
        except requests.RequestException as exc:
            _logger.warning("Request failed for roll %s (attempt %s): %s", roll_no, attempt, exc)
            if attempt >= max_attempts:
                return {
                    "success": "False",
                    "error": "Request failed after retries",
                    "error_type": "request",
                }
        except Exception as exc:
            _logger.exception("Unexpected error for roll %s: %s", roll_no, exc)
            return {
                "success": "False",
                "error": "Unexpected parsing error",
                "error_type": "unexpected",
            }

    return {
        "success": "False",
        "error": "Max attempts exceeded",
        "error_type": "attempts",
    }


def save_results(rows: Iterable[Dict[str, str]], csv_filename: str = "Student_Results.csv") -> None:
    rows_list = list(rows)
    if not rows_list:
        return

    fieldnames = ["Roll_Number", "Name", "Father_Name", "Total_Marks", "Status", "Subject_Pass"]
    if os.path.isfile(csv_filename):
        try:
            with open(csv_filename, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                existing_headers = next(reader, None)
                if existing_headers:
                    fieldnames = existing_headers
        except Exception:
            pass

    with open(csv_filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        if os.path.getsize(csv_filename) == 0:
            writer.writeheader()
        writer.writerows(rows_list)


def scrape_roll_numbers_parallel(
    roll_numbers: List[int],
    course: str,
    exam_type: str,
    year: str,
    max_workers: int = DEFAULT_MAX_WORKERS,
    delay_range: Tuple[int, int] = DEFAULT_DELAY_RANGE,
    csv_file: str = "Student_Results.csv",
    progress_callback: Optional[callable] = None,
    use_tqdm: bool = False,
    flush_every: int = DEFAULT_FLUSH_EVERY,
) -> Dict[str, object]:
    setup_logging()

    if not roll_numbers:
        return {"total": 0, "success": 0, "failed": 0, "failed_rolls": []}

    max_workers = max(1, min(max_workers, len(roll_numbers)))
    delay_range = normalize_delay_range(delay_range)
    flush_every = max(1, int(flush_every))

    results: List[Dict[str, str]] = []
    failed_rolls: List[int] = []
    pending_rows: List[Dict[str, str]] = []

    def worker(roll_no: int) -> Tuple[int, Dict[str, str]]:
        result = process_roll_number(
            roll_no=roll_no,
            course=course,
            exam_type=exam_type,
            year=year,
            delay_range=delay_range,
        )
        return roll_no, result

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for roll in roll_numbers:
            futures.append(executor.submit(worker, roll))

        iterator = as_completed(futures)
        if use_tqdm:
            iterator = tqdm(iterator, total=len(futures), desc="Scraping", unit="roll")

        for future in iterator:
            roll_no, result = future.result()
            if result.get("success") == "True":
                results.append(result)
                pending_rows.append(result)
                if len(pending_rows) >= flush_every:
                    save_results(pending_rows, csv_file)
                    pending_rows.clear()
            else:
                failed_rolls.append(roll_no)
                _logger.info("Failed roll %s: %s", roll_no, result.get("error"))

            if progress_callback:
                progress_callback(roll_no, result)

        if pending_rows:
            save_results(pending_rows, csv_file)
            pending_rows.clear()

    if failed_rolls:
        with open("failed_rolls.txt", "w", encoding="utf-8") as file:
            file.write(",".join(str(roll) for roll in failed_rolls))

    return {
        "total": len(roll_numbers),
        "success": len(results),
        "failed": len(failed_rolls),
        "failed_rolls": failed_rolls,
    }


def scrape_bise_lahore_requests(
    roll_no: str,
    course: str = "HSSC",
    exam_type: str = "2",
    year: str = "2024",
) -> bool:
    result = process_roll_number(
        roll_no=int(roll_no),
        course=course,
        exam_type=exam_type,
        year=year,
    )
    if result.get("success") == "True":
        save_results([result])
        return True
    return False


def close_browser() -> None:
    return None


if __name__ == "__main__":
    setup_logging()
    print("-" * 50)
    print("BISE Lahore Requests Scraper")
    print("-" * 50)

    print("\n--- Enter Roll Numbers ---")
    print("You can enter a single number (123456), multiple numbers split by a comma (123456, 123457),")
    print("or a range (123456-123460) to scrape multiple students in a row.")
    roll_input = input("Roll Numbers: ")

    roll_numbers_to_check = load_roll_numbers(roll_input)
    if not roll_numbers_to_check:
        print("No valid roll numbers provided. Exiting.")
        raise SystemExit(1)

    print("\n--- Select Course ---")
    course_type = input("Enter 'SSC' for Matric, or 'HSSC' for Intermediate (Default is HSSC): ").upper()
    if not course_type or course_type not in ["SSC", "HSSC"]:
        course_type = "HSSC"
        print("Defaulting to: HSSC (Intermediate)")

    print("\n--- Select Year ---")
    exam_year = input("Enter Year (e.g., 2024 or 2025): ")
    if not exam_year:
        exam_year = "2024"
        print("Defaulting to: 2024")

    print("\n--- Select Exam Type ---")
    print("0 = Supplementary")
    print("1 = Part-I (Annual)")
    print("2 = Part-II (Annual)")
    exam_type_input = input("Enter Exam Type (0, 1, or 2): ")
    if not exam_type_input or exam_type_input not in ["0", "1", "2"]:
        exam_type_input = "2"
        print("Defaulting to: 2 (Part-II Annual)")

    print("\n--- Concurrency ---")
    workers_input = input("Max parallel workers (default 5): ").strip()
    max_workers = int(workers_input) if workers_input.isdigit() else DEFAULT_MAX_WORKERS

    summary = scrape_roll_numbers_parallel(
        roll_numbers=roll_numbers_to_check,
        course=course_type,
        exam_type=exam_type_input,
        year=exam_year,
        max_workers=max_workers,
        use_tqdm=True,
    )

    print("\n" + "=" * 50)
    print("Scraping Complete")
    print(f"Successfully processed {summary['success']} out of {summary['total']} roll numbers.")
    print("Check Student_Results.csv for the data.")
    if summary["failed_rolls"]:
        print("Failed roll numbers saved to failed_rolls.txt")
    print("=" * 50)
