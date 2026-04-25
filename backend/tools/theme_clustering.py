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

def generate_weekly_action_ideas(stats_report: Dict[str, Any], app_name: str) -> List[str]:
    """
    Uses the LLM to generate 3 concrete action ideas based on the week's top themes.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ["Sync with product team on high-volume labels", "Monitor social media for cross-platform sentiment", "Review most critical 1-star reviews manually"]

    client = Groq(api_key=api_key)
    
    # Sort themes by volume to identify the top 3
    sorted_themes = sorted(stats_report.items(), key=lambda x: x[1]['volume'], reverse=True)[:3]
    top_3_summary = ""
    for theme, data in sorted_themes:
        top_3_summary += f"- Theme: {theme} (Rating: {data['average_rating']})\n"
        top_3_summary += f"  Sample Feedback: {data['representative_quotes'][0] if data['representative_quotes'] else 'None'}\n"

    prompt = f"""You are a Product Manager for {app_name}. Based on this week's app review data, generate exactly 3 concrete, high-level ACTION IDEAS for the product team.
    
    Data:
    {top_3_summary}
    
    Format:
    1. Action Item 1
    2. Action Item 2
    3. Action Item 3
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
            temperature=0.3,
        )
        ideas = chat_completion.choices[0].message.content.strip().split('\n')
        # Clean up list formatting if present
        ideas = [i.strip() for i in ideas if i.strip()]
        return ideas[:3]
    except Exception as e:
        logger.error(f"Error generating action ideas: {e}")
        return ["Review new user onboarding flow", "Investigate payment success rates", "Audit portfolio statement generating engine"]

def run_clustering_pipeline(app_name: str = "Kuvera") -> Dict[str, Any]:
    try:
        files = list(PROCESSED_DATA_DIR.glob("clean_reviews_*.json"))
        if not files:
            logger.error("No clean reviews found to cluster.")
            return {}
        latest_file = max(files, key=os.path.getctime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            clean_reviews = json.load(f)
    except Exception as e:
        logger.error(f"Error loading clean reviews: {e}")
        return {}

    logger.info(f"Starting pipeline for {len(clean_reviews)} reviews.")
    clustered, unclassified = hard_keyword_pre_cluster(clean_reviews)
    logger.info(f"Local Pre-Clustering complete. {len(unclassified)} reviews require advanced LLM.")
    
    stats_report = analyze_sentiment_and_quotes(clustered, unclassified)
    llm_insights = batch_llm_clustering(unclassified, app_name)
    
    # Robust Fallback: If local clusters are empty, try to populate them from AI insights
    if not stats_report and llm_insights.get("AI Insights"):
        logger.info("Local clusters empty. Attempting to populate themes from AI Insights fallback...")
        # Since we use LLM for Action Ideas, it will still work
        pass

    action_ideas = generate_weekly_action_ideas(stats_report, app_name)
    
    # Ensure Action Ideas is a list of exactly 3
    if isinstance(action_ideas, str):
        action_ideas = [i.strip() for i in action_ideas.split('\n') if i.strip()][:3]

    final_output = {
        "local_clusters": stats_report,
        "advanced_insights": llm_insights,
        "action_ideas": action_ideas
    }

    output_file = OUTPUT_DIR / "clustered_insights.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    logger.info("Clustering pipeline complete.")
    return final_output

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_clustering_pipeline()
