import schedule
import time
import logging
import json
from datetime import datetime

# Import our own modules
from extract import scrape_all
from transform import clean_data
from load import load_to_database

# -------------------------------------------------------
# STEP 1: Set up logging
# All events (success, errors) are written to pipeline.log
# You can open this file to see what happened and when
# -------------------------------------------------------
logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)


# -------------------------------------------------------
# STEP 2: Define the full pipeline as one function
# This is what runs automatically on a schedule
# Each step is wrapped in try/except so one failure
# doesn't crash the whole pipeline silently
# -------------------------------------------------------
def run_pipeline():
    start = datetime.now()
    logging.info("Pipeline started")
    print(f"[{start}] Pipeline started...")

    try:
        # --- Stage 1: Scrape ---
        logging.info("Stage 1: Scraping...")
        books = scrape_all()
        with open("raw_books.json", "w") as f:
            json.dump(books, f, indent=2)
        logging.info(f"Scraped {len(books)} books")

    except Exception as e:
        logging.error(f"Stage 1 FAILED: {e}")
        print(f"Scraping failed: {e}")
        return  # Stop pipeline if scraping fails

    try:
        # --- Stage 2: Clean ---
        logging.info("Stage 2: Cleaning data...")
        clean_data("raw_books.json")
        logging.info("Data cleaned and saved to clean_books.csv")

    except Exception as e:
        logging.error(f"Stage 2 FAILED: {e}")
        print(f"Cleaning failed: {e}")
        return

    try:
        # --- Stage 3: Load to DB ---
        logging.info("Stage 3: Loading to database...")
        load_to_database("clean_books.csv")
        logging.info("Data loaded to database")

    except Exception as e:
        logging.error(f"Stage 3 FAILED: {e}")
        print(f"Database load failed: {e}")
        return

    duration = (datetime.now() - start).seconds
    logging.info(f"Pipeline completed in {duration}s")
    print(f"Pipeline complete! Took {duration} seconds.")


# -------------------------------------------------------
# STEP 3: Schedule the pipeline to run every 24 hours
# You can change this to .hours(6), .minutes(30), etc.
# The while loop keeps the script alive and checks the schedule
# -------------------------------------------------------
if __name__ == "__main__":
    print("Pipeline scheduler started. Press Ctrl+C to stop.")
    logging.info("Scheduler started")

    # Run once immediately when you start the script
    run_pipeline()

    # Then schedule it to repeat every 24 hours
    schedule.every(24).hours.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if a job is due
