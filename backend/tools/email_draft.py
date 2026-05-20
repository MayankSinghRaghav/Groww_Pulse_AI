import json
import logging
import datetime
import os
from groq import Groq
from typing import List, Dict, Any
from config.settings import OUTPUT_DIR, APP_NAME, MODEL_NAME
from config.prompts import TONE_MAP

logger = logging.getLogger("email_draft")

BACKEND_URL = os.getenv("BACKEND_URL", "https://kuvera-pulse.onrender.com")

ROLE_SHORT_INTRO = {
    "Product Team": "Hi team,\n\nPlease find this week's Groww Pulse Note attached — it highlights the top 3 user-reported engineering pain points from this week's Play Store reviews, along with recommended sprint items.\n\nClick the link below to download your briefing PDF.",
    "Support Team": "Hi Support team,\n\nThis week's Groww Pulse Note is ready. It covers the top 3 escalation themes your agents will likely encounter, real user quotes to guide your empathy scripts, and 3 action points.\n\nClick the link below to download your briefing PDF.",
    "Leadership": "Hi,\n\nThis week's Groww Pulse Note summarises the most critical signals from our app reviews. It includes the top 3 retention risk areas and one strategic recommendation.\n\nClick the link below to download your briefing PDF.",
}


def draft_email_variants(insights_data: dict, pdf_paths: dict = None) -> List[Dict[str, Any]]:
    """Generates 3 short role-specific emails with a link to the PDF note."""
    week_date = datetime.datetime.now().strftime("%B %d, %Y")
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    email_drafts = []

    for role in TONE_MAP.keys():
        intro = ROLE_SHORT_INTRO.get(role, "Please find this week's pulse note below.")
        pdf_filename = f"Groww_Pulse_{role.replace(' ', '_')}_{today_str}.pdf"
        download_link = f"{BACKEND_URL}/mcp/download-note/{pdf_filename}"

        body = f"""{intro}

📎 Download PDF Note: {download_link}

---
This note covers:
  • Top 3 critical user-feedback themes
  • 3 real user quotes
  • 3 recommended actions for your team

Regards,
Groww Pulse AI Engine
(Automated weekly digest — Groww)"""

        email_drafts.append({
            "role": role,
            "subject": f"Weekly Groww Pulse for {role}",
            "body": body,
            "pdf_filename": pdf_filename,
            "download_link": download_link,
            "timestamp": datetime.datetime.now().isoformat()
        })

    return email_drafts


def run_email_drafting():
    logger.info("Starting email drafting phase.")
    input_file = OUTPUT_DIR / "clustered_insights.json"
    if not input_file.exists():
        logger.error(f"Missing input data at {input_file}")
        return
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            insights_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read insights data: {e}")
        return

    # Generate PDFs first
    try:
        from tools.pdf_note import generate_all_pdf_notes
        pdf_paths = generate_all_pdf_notes(insights_data, insights_data.get("action_ideas", {}))
        logger.info(f"Generated {len(pdf_paths)} PDF notes.")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        pdf_paths = {}

    # Generate short emails with PDF links
    drafts = draft_email_variants(insights_data, pdf_paths)
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
