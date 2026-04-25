import json
import logging
import datetime
import os
from groq import Groq
from typing import List, Dict, Any
from config.settings import OUTPUT_DIR, APP_NAME, MODEL_NAME
from config.prompts import SYSTEM_PROMPT_EMAIL, TONE_MAP

logger = logging.getLogger("email_draft")

def draft_email_variants(insights_data: dict) -> List[Dict[str, Any]]:
    """
    Generates 3 email drafts for different stakeholder roles using direct Groq client.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not found. Skipping automated email drafting.")
        return []

    client = Groq(api_key=api_key)

    # Prepare a condensed summary for the LLM
    summary_text = ""
    local_clusters = insights_data.get("local_clusters", {})
    for theme, data in local_clusters.items():
        summary_text += f"- {theme}: {data['volume']} reviews, Avg Rating: {data['average_rating']}\n"

    email_drafts = []
    
    for role, tone in TONE_MAP.items():
        logger.info(f"Drafting email for {role}...")
        prompt = SYSTEM_PROMPT_EMAIL.format(
            role=role,
            tone=tone,
            app_name=APP_NAME,
            insights=summary_text
        )
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.7,
            )
            email_drafts.append({
                "role": role,
                "subject": f"[{APP_NAME}] Weekly Review Pulse - {role} Focus",
                "body": chat_completion.choices[0].message.content,
                "timestamp": datetime.datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to draft email for {role}: {e}")

    return email_drafts

def run_email_drafting():
    logger.info("Starting email drafting phase.")
    input_file = OUTPUT_DIR / "clustered_insights.json"
    if not input_file.exists():
        logger.error(f"Missing input data. Ensure Phase 3 has run and generated {input_file}")
        return
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            insights_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read insights data: {e}")
        return

    drafts = draft_email_variants(insights_data)
    if drafts:
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        output_file = OUTPUT_DIR / f"{APP_NAME}_stakeholder_emails_{today_str}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(drafts, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(drafts)} email drafts to {output_file}")
    logger.info("Email drafting pipeline complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_email_drafting()
