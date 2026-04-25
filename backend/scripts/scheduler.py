import schedule
import time
import subprocess
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("scheduler")

def run_weekly_job():
    logger.info("⏰ It is Monday 9:00 AM. Triggering Kuvera Weekly Pulse Pipeline...")
    try:
        # Trigger the runner script
        # We use sys.executable to ensure it uses the same python environment
        result = subprocess.run(
            [sys.executable, "scripts/run_weekly_pulse.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Pipeline output: {result.stdout}")
        logger.info("✅ Weekly job completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Weekly job failed: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in scheduler: {e}")

# Schedule for every Monday at 09:00
schedule.every().monday.at("09:00").do(run_weekly_job)

if __name__ == "__main__":
    logger.info("🚀 Scheduler started. Waiting for Monday 9:00 AM...")
    
    # Optional: Run once on startup if needed for testing
    # run_weekly_job()
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute
