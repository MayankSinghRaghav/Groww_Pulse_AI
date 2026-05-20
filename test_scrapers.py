import datetime
import logging
import sys
import os

sys.path.append(os.path.abspath('backend'))
logging.basicConfig(level=logging.INFO)

from tools.review_ingestion import fetch_play_store_reviews, fetch_app_store_reviews

cutoff = datetime.datetime.now() - datetime.timedelta(days=7)

print("1. Testing Play Store reviews fetch (count=5)...")
play_reviews = fetch_play_store_reviews(cutoff, count=5)
print(f"Play Store fetched: {len(play_reviews)} reviews.")
if play_reviews:
    print(f"Sample: {play_reviews[0]}")

print("\n2. Testing App Store reviews fetch (count=5)...")
app_reviews = fetch_app_store_reviews(cutoff, count=5)
print(f"App Store fetched: {len(app_reviews)} reviews.")
if app_reviews:
    print(f"Sample: {app_reviews[0]}")
