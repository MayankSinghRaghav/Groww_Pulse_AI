import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Application Configuration
APP_NAME = os.getenv("APP_NAME", "Kuvera")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Path Configurations
DATA_DIR = BASE_DIR / "data"
RAW_REVIEWS_DIR = DATA_DIR / "raw_reviews"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", DATA_DIR / "outputs"))
LOG_DIR = Path(os.getenv("LOG_DIR", DATA_DIR / "logs"))

# Ensure directories exist
for directory in [RAW_REVIEWS_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Analysis Settings
REVIEW_WINDOW_WEEKS = 8
TARGET_REVIEW_COUNT = 1000
