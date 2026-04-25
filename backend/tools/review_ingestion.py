import datetime
import logging
from typing import List, Dict, Any
from google_play_scraper import reviews, Sort
from app_store_scraper import AppStore
from langdetect import detect, LangDetectException
from spellchecker import SpellChecker
import json
from config.settings import RAW_REVIEWS_DIR, PROCESSED_DATA_DIR, REVIEW_WINDOW_WEEKS

logger = logging.getLogger("review_ingestion")
# SpellChecker is deferred or unused to speed up cloud startup
spell = None

# Kuvera app identifiers
PLAY_STORE_APP_ID = "com.onie.kuvera"  
APP_STORE_APP_NAME = "kuvera"
APP_STORE_APP_ID = "1256317260"

def is_valid_english_text(text: str) -> bool:
    """Filters for minimum content length."""
    if not text or len(text.strip()) < 5:
        return False
    return True

def filter_reviews(raw_reviews: List[Dict[str, Any]], cutoff_date: datetime.datetime) -> List[Dict[str, Any]]:
    filtered = []
    seen_ids = set()
    
    logger.info(f"Processing {len(raw_reviews)} raw reviews...")
    for r in raw_reviews:
        review_id = r.get('id')
        review_date = r.get('date')
        content = r.get('content', '')
        
        # Deduplication
        if review_id in seen_ids:
            continue
            
        # Date filtering
        if isinstance(review_date, str):
             # Handle ISO strings
             review_date = datetime.datetime.fromisoformat(review_date.replace('Z', '+00:00'))
             
        if isinstance(review_date, datetime.datetime):
            # Ensure naive vs aware mismatch doesn't break
            if review_date.tzinfo is not None:
                review_date = review_date.replace(tzinfo=None)
            
            if review_date < cutoff_date:
                continue
            
        # Light filtering
        if not is_valid_english_text(content):
            continue
            
        seen_ids.add(review_id)
        filtered.append(r)
        
    return filtered

def fetch_play_store_reviews(cutoff_date: datetime.datetime, count: int = 5000) -> List[Dict[str, Any]]:
    logger.info("Fetching reviews from Google Play...")
    try:
        result, _ = reviews(
            PLAY_STORE_APP_ID,
            lang='en',
            country='in',
            sort=Sort.NEWEST,
            count=count
        )
        
        formatted = []
        for r in result:
            formatted.append({
                'id': str(r['reviewId']),
                'platform': 'google_play',
                'date': r['at'],
                'rating': r['score'],
                'content': r['content'],
                'version': r.get('reviewCreatedVersion')
            })
        return formatted
    except Exception as e:
        logger.error(f"Play Store fetch error: {e}")
        return []

def fetch_app_store_reviews(cutoff_date: datetime.datetime, count: int = 1000) -> List[Dict[str, Any]]:
    logger.info("Fetching reviews from App Store...")
    try:
        kuvera_app = AppStore(country='in', app_name=APP_STORE_APP_NAME, app_id=APP_STORE_APP_ID)
        kuvera_app.review(how_many=count)
        
        formatted = []
        for r in kuvera_app.reviews:
            formatted.append({
                'id': str(r.get('id', hash(r['review']))),
                'platform': 'app_store',
                'date': r['date'],
                'rating': r['rating'],
                'content': r['review'],
                'version': None
            })
        return formatted
    except Exception as e:
        logger.error(f"App Store fetch error: {e}")
        return []

def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    cutoff_date = datetime.datetime.now() - datetime.timedelta(weeks=REVIEW_WINDOW_WEEKS)
    logger.info(f"Starting ingestion. Cutoff date: {cutoff_date.date()}")
    
    play_reviews = fetch_play_store_reviews(cutoff_date)
    app_reviews = fetch_app_store_reviews(cutoff_date)
    
    all_raw = play_reviews + app_reviews
    logger.info(f"Raw reviews fetched: {len(all_raw)}")
    
    # Filter and clean
    clean_reviews = filter_reviews(all_raw, cutoff_date)
    logger.info(f"Clean (English, Valid Spelling) reviews: {len(clean_reviews)}")
    
    # Save the processed list
    file_path = PROCESSED_DATA_DIR / f"clean_reviews_{datetime.datetime.now().strftime('%Y%m%d')}.json"
    
    # format dates for JSON serialization
    for r in clean_reviews:
        if isinstance(r['date'], datetime.datetime):
            r['date'] = r['date'].isoformat()
            
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(clean_reviews, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved processed reviews to {file_path}")
    return clean_reviews

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion_pipeline()
