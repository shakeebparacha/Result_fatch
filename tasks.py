import os

from rq import get_current_job

from scraper import load_roll_numbers, scrape_roll_numbers_parallel


def run_scrape_job(roll_numbers_input: str, course: str, exam_year: str, exam_type: str, csv_file: str):
    job = get_current_job()
    roll_list, duplicates, invalids = load_roll_numbers(roll_numbers_input, return_details=True)

    total = len(roll_list)
    job.meta["total"] = total
    job.meta["processed"] = 0
    job.meta["success"] = 0
    job.meta["message"] = f"Queued {total} roll numbers for scraping."
    job.meta["duplicate_rolls"] = duplicates
    job.meta["invalid_rolls"] = invalids
    job.save_meta()

    def progress_callback(roll_no, result):
        job.meta["processed"] = job.meta.get("processed", 0) + 1
        if result.get("success") == "True":
            job.meta["success"] = job.meta.get("success", 0) + 1
        job.meta["message"] = (
            f"Completed {job.meta['processed']} of {total} roll numbers. "
            f"Last roll: {roll_no}"
        )
        job.save_meta()

    max_workers = int(os.getenv("SCRAPER_MAX_WORKERS", "10"))

    summary = scrape_roll_numbers_parallel(
        roll_numbers=roll_list,
        course=course,
        exam_type=exam_type,
        year=exam_year,
        max_workers=max_workers,
        csv_file=csv_file,
        progress_callback=progress_callback,
        use_tqdm=False,
    )

    job.meta["processed"] = summary.get("total", total)
    job.meta["success"] = summary.get("success", 0)
    job.meta["failed_rolls"] = summary.get("failed_rolls", [])
    job.meta["message"] = (
        f"Finished! Successfully scraped {summary.get('success', 0)} out of {summary.get('total', total)} roll numbers."
    )
    job.save_meta()

    return summary
