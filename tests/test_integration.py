import pytest
import json
from unittest.mock import patch, MagicMock
from tools.review_ingestion import filter_reviews
from tools.theme_clustering import hard_keyword_pre_cluster
import datetime

@pytest.fixture
def mock_reviews():
    return [
        {"id": "1", "content": "This app is great for mutual funds!", "date": datetime.datetime.now(), "rating": 5},
        {"id": "2", "content": "App keeps crashing every time I open it.", "date": datetime.datetime.now(), "rating": 1},
        {"id": "3", "content": "Confusing UI, hard to find portfolio.", "date": datetime.datetime.now(), "rating": 3},
        {"id": "4", "content": "I love the new analytics feature.", "date": datetime.datetime.now(), "rating": 4},
        {"id": "5", "content": "Customer support is very helpful.", "date": datetime.datetime.now(), "rating": 2},
    ]

def test_language_and_spelling_filter():
    """Test that the ingestion filter correctly handles language and spelling (mocked)."""
    bad_data = [
        {"id": "6", "content": "asdfasdfasdfasdf", "date": datetime.datetime.now()}, # Gibberish
        {"id": "7", "content": "C'est une excellente application", "date": datetime.datetime.now()}, # French
    ]
    
    with patch("tools.review_ingestion.is_valid_english_text") as mock_val:
        # Mock logic: Review 7 is French, 6 is gibberish
        mock_val.side_effect = lambda text: "app" in text.lower() or "support" in text.lower()
        
        cutoff = datetime.datetime.now() - datetime.timedelta(days=1)
        # Assuming the mock_reviews from fixture are passed manually for simplicity here
        mock_list = [
            {"id": "1", "content": "This is a great app", "date": datetime.datetime.now()},
            {"id": "6", "content": "asdfasdf", "date": datetime.datetime.now()}
        ]
        filtered = filter_reviews(mock_list, cutoff)
        assert len(filtered) == 1
        assert filtered[0]['id'] == "1"

def test_keyword_clustering(mock_reviews):
    """Test that reviews are correctly mapped to our taxonomy keywords."""
    clustered, unclassified = hard_keyword_pre_cluster(mock_reviews)
    
    # "crashing" should go to Performance & Stability
    assert len(clustered["Performance & Stability"]) == 1
    assert clustered["Performance & Stability"][0]["id"] == "2"
    
    # "support" should go to Customer Support
    assert len(clustered["Customer Support"]) == 1
    assert clustered["Customer Support"][0]["id"] == "5"

def test_unclassified_logic():
    """Test that reviews without keywords end up in unclassified for LLM processing."""
    mixed_reviews = [{"id": "99", "content": "Something very unique feedback that has no keywords."}]
    clustered, unclassified = hard_keyword_pre_cluster(mixed_reviews)
    assert len(unclassified) == 1
    assert unclassified[0]["id"] == "99"


def test_demo_mode_off_fails_loud(monkeypatch):
    """Empty scrape must raise (not silently return fake data) when DEMO_MODE is off."""
    from tools import theme_clustering as tc
    monkeypatch.setattr(tc, "DEMO_MODE", False)
    with pytest.raises(RuntimeError):
        tc._fallback_or_fail("0 reviews found after scraping.", {"local_clusters": {}})


def test_demo_mode_on_returns_fallback(monkeypatch):
    """With DEMO_MODE on, the canned fallback is returned instead of raising."""
    from tools import theme_clustering as tc
    monkeypatch.setattr(tc, "DEMO_MODE", True)
    monkeypatch.setattr(tc, "_save_and_return", lambda data: None)
    fallback = {"local_clusters": {"demo": 1}}
    assert tc._fallback_or_fail("0 reviews found after scraping.", fallback) is fallback
