import json
with open('backend/data/processed/clean_reviews_20260516.json', 'r', encoding='utf-8') as f:
    reviews = json.load(f)
print(f"Number of reviews: {len(reviews)}")
