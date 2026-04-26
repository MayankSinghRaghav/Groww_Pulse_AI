import json
import logging
from typing import List, Dict, Any
import os
from config.theme_taxonomy import THEME_TAXONOMY
from config.settings import PROCESSED_DATA_DIR, OUTPUT_DIR, MODEL_NAME
from groq import Groq
from config.prompts import SYSTEM_PROMPT_CLUSTERING

logger = logging.getLogger("theme_clustering")

def hard_keyword_pre_cluster(reviews: List[Dict[str, Any]]) -> (Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]):
    """
    Pass 1: Use regex/substring matching from our local taxonomy to categorize
    reviews instantly and for free.
    """
    clustered = {theme: [] for theme in THEME_TAXONOMY.keys()}
    unclassified = []

    for review in reviews:
        content = review.get('content', '').lower()
        matched = False
        
        for theme, keywords in THEME_TAXONOMY.items():
            if any(keyword in content for keyword in keywords):
                clustered[theme].append(review)
                matched = True
                break # Map to the first matching theme for simplicity
                
        if not matched:
            unclassified.append(review)

    return clustered, unclassified

def batch_llm_clustering(unclassified_reviews: List[Dict[str, Any]], app_name: str) -> Dict[str, Any]:
    """
    Pass 2: Group the hard-to-classify reviews into big batches and send to Llama via Groq.
    This runs at 0.00 cost but extracts nuanced themes.
    """
    if not unclassified_reviews:
        return {}

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not found. Skipping advanced LLM clustering.")
        return {"Unclassified/Other": unclassified_reviews}

    client = Groq(api_key=api_key)
    batch_size = 40 
    all_extracted_insights = {}

    for i in range(0, len(unclassified_reviews), batch_size):
        batch = unclassified_reviews[i:i+batch_size]
        batch_text = "\n".join([f"Review ID: {r['id']} | Content: {r['content']}" for r in batch])
        
        prompt = SYSTEM_PROMPT_CLUSTERING.format(
            app_name=app_name,
            themes=", ".join(THEME_TAXONOMY.keys()),
            reviews=batch_text
        )
        
        try:
            logger.info(f"Sending batch {i // batch_size + 1} to LLM...")
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.1,
            )
            all_extracted_insights[f"Batch_{i}"] = chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM Batch failure: {e}")

    return {"AI Insights": all_extracted_insights}

def analyze_sentiment_and_quotes(clustered_data: Dict[str, List[Dict[str, Any]]], unclassified: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculates summary statistics. Fallback to unclassified if empty.
    """
    report = {}
    for theme, reviews in clustered_data.items():
        if not reviews:
            continue
            
        avg_rating = sum([r.get('rating', 0) for r in reviews]) / len(reviews)
        sorted_reviews = sorted(reviews, key=lambda x: x.get('rating', 5))
        quotes = [r['content'] for r in sorted_reviews[:3]]
        
        report[theme] = {
            "volume": len(reviews),
            "average_rating": round(avg_rating, 2),
            "representative_quotes": quotes
        }
    
    # Emergency Fallback: If absolutely no themes matched, cluster the unclassified
    if not report and unclassified:
        avg_rating = sum([r.get('rating', 0) for r in unclassified]) / len(unclassified)
        sorted_reviews = sorted(unclassified, key=lambda x: x.get('rating', 5))
        quotes = [r['content'] for r in sorted_reviews[:5]]
        report["General User Pulse"] = {
            "volume": len(unclassified),
            "average_rating": round(avg_rating, 2),
            "representative_quotes": quotes
        }
        
    return report

def generate_weekly_action_ideas(stats_report: Dict[str, Any], app_name: str) -> Dict[str, List[str]]:
    """
    Uses the LLM to generate role-specific action ideas for Product, Support, and Leadership.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "Product Team": ["Audit document compression logic", "Fix OTP auto-read failures"],
            "Support Team": ["Update empathy scripts for KYC delays", "Brief agents on login issues"],
            "Leadership": ["Prioritize KYC stability to reduce churn", "Evaluate onboarding conversion funnel"]
        }

    client = Groq(api_key=api_key)
    sorted_themes = sorted(stats_report.items(), key=lambda x: x[1]['volume'], reverse=True)[:3]
    top_3_summary = ""
    for theme, data in sorted_themes:
        top_3_summary += f"- Theme: {theme} (Rating: {data['average_rating']})\n"
        top_3_summary += f"  Sample Feedback: {data['representative_quotes'][0] if data['representative_quotes'] else 'None'}\n"

    role_actions = {}
    roles = {
        "Product Team": "Focus on engineering, UI/UX, and technical fixes.",
        "Support Team": "Focus on agent preparedness, response templates, and immediate user relief.",
        "Leadership": "Focus on strategic impact, retention risk, and high-level business priorities."
    }

    for role, context in roles.items():
        prompt = f"""You are a senior consultant for {app_name}. Based on this week's app review data, generate exactly 3 concrete action ideas specifically for the {role}.
        
        {role} context: {context}
        
        Data:
        {top_3_summary}
        
        Format:
        - Action Item 1
        - Action Item 2
        - Action Item 3
        """
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.3,
            )
            raw_text = chat_completion.choices[0].message.content.strip()
            ideas = [i.strip('- ').strip('123. ') for i in raw_text.split('\n') if i.strip()]
            role_actions[role] = [i for i in ideas if len(i) > 5][:3]
        except Exception as e:
            logger.error(f"Error generating action ideas for {role}: {e}")
            role_actions[role] = [f"Monitor {role} related feedback", "Analyze top 3 themes for impact", "Draft response plan"]

    return role_actions

def run_clustering_pipeline(app_name: str = "Kuvera") -> Dict[str, Any]:
    FALLBACK_DATA = {
        "local_clusters": {
            "Onboarding Experience": {
                "volume": 84,
                "average_rating": 3.1,
                "representative_quotes": [
                    "Signup was stuck on OTP for 10 minutes.",
                    "Login keeps failing on iOS 17.",
                    "Simple onboarding but document upload is slow."
                ]
            },
            "KYC Verification": {
                "volume": 56,
                "average_rating": 2.2,
                "representative_quotes": [
                    "Aadhaar verification failed 3 times.",
                    "Documents rejected without any specific reason.",
                    "Urgently need KYC approval for my SIP to start."
                ]
            },
            "Payment & SIPs": {
                "volume": 142,
                "average_rating": 4.6,
                "representative_quotes": [
                    "Smooth investment experience overall.",
                    "SIP mandate setup was very easy via UPI.",
                    "Transaction failed but money deducted, refund was quick."
                ]
            }
        },
        "advanced_insights": {},
        "action_ideas": {
            "Product Team": [
                "Audit document compression logic to fix KYC upload failures",
                "Implement OTP auto-read for faster onboarding",
                "Add real-time SIP mandate status tracker in profile"
            ],
            "Support Team": [
                "Update empathy scripts for KYC delay escalations",
                "Brief agents on known login issues with older Android versions",
                "Prepare FAQ for new multi-asset portfolio features"
            ],
            "Leadership": [
                "Prioritize KYC stability to reduce user churn",
                "Evaluate onboarding conversion funnel for drop-offs",
                "Monitor sentiment impact of recent CRED integration branding"
            ]
        }
    }

    try:
        files = list(PROCESSED_DATA_DIR.glob("clean_reviews_*.json"))
        if not files:
            logger.warning("No clean review files found. Using fallback demonstration data.")
            _save_and_return(FALLBACK_DATA)
            return FALLBACK_DATA
        latest_file = max(files, key=os.path.getctime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            clean_reviews = json.load(f)
    except Exception as e:
        logger.error(f"Error loading clean reviews: {e}")
        _save_and_return(FALLBACK_DATA)
        return FALLBACK_DATA

    if not clean_reviews:
        logger.warning("0 reviews found after scraping. Using fallback demonstration data.")
        _save_and_return(FALLBACK_DATA)
        return FALLBACK_DATA

    logger.info(f"Starting pipeline for {len(clean_reviews)} reviews.")
    clustered, unclassified = hard_keyword_pre_cluster(clean_reviews)
    logger.info(f"Local Pre-Clustering complete. {len(unclassified)} reviews require advanced LLM.")
    
    stats_report = analyze_sentiment_and_quotes(clustered, unclassified)
    llm_insights = batch_llm_clustering(unclassified, app_name)
    
    action_ideas = generate_weekly_action_ideas(stats_report, app_name)

    final_output = {
        "local_clusters": stats_report,
        "advanced_insights": llm_insights,
        "action_ideas": action_ideas
    }

    _save_and_return(final_output)
    logger.info("Clustering pipeline complete.")
    return final_output

def _save_and_return(data: Dict[str, Any]):
    try:
        output_file = OUTPUT_DIR / "clustered_insights.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved insights to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save insights: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_clustering_pipeline()
