import json
import logging
import datetime
import os
from groq import Groq
from typing import List, Dict, Any
from config.settings import OUTPUT_DIR, APP_NAME, MODEL_NAME
from config.prompts import SYSTEM_PROMPT_EMAIL, TONE_MAP

logger = logging.getLogger("email_draft")


def _build_note_prompt(role: str, tone: str, insights_data: dict) -> str:
    """Build a structured prompt using real insights data."""
    local_clusters = insights_data.get("local_clusters", {})
    action_ideas = insights_data.get("action_ideas", [])
    week_date = datetime.datetime.now().strftime("%B %d, %Y")

    # Sort themes by volume (descending) and take top 3
    sorted_themes = sorted(local_clusters.items(), key=lambda x: x[1].get("volume", 0), reverse=True)[:3]

    # Collect top 3 quotes across all themes
    all_quotes = []
    for _, data in sorted_themes:
        all_quotes.extend(data.get("representative_quotes", []))
    all_quotes = [q for q in all_quotes if q and len(q.strip()) > 10][:3]
    while len(all_quotes) < 3:
        all_quotes.append("Users appreciate the clean interface and fast performance.")

    # Pad themes if fewer than 3
    while len(sorted_themes) < 3:
        sorted_themes.append(("General Feedback", {"volume": 0, "average_rating": 0, "representative_quotes": []}))

    total_reviews = sum(d.get("volume", 0) for _, d in local_clusters.items())

    # Build theme summaries (short 1-line per theme)
    def theme_summary(name, data):
        rating = data.get("average_rating", 0)
        if rating < 2.5:
            return f"Critical pain point — users are highly frustrated with {name.lower()}."
        elif rating < 3.5:
            return f"Mixed sentiment — some friction in the {name.lower()} experience."
        else:
            return f"Positive signal — users are largely satisfied with {name.lower()}."

    # Pad action ideas
    while len(action_ideas) < 3:
        action_ideas.append("Review and prioritize top user-reported issues in the next sprint.")
    actions = action_ideas[:3]

    t1_name, t1_data = sorted_themes[0]
    t2_name, t2_data = sorted_themes[1]
    t3_name, t3_data = sorted_themes[2]

    prompt = SYSTEM_PROMPT_EMAIL.format(
        role=role,
        tone=tone,
        week_date=week_date,
        total_reviews=total_reviews,
        theme1_name=t1_name,
        theme1_volume=t1_data.get("volume", 0),
        theme1_rating=t1_data.get("average_rating", 0),
        theme1_summary=theme_summary(t1_name, t1_data),
        theme2_name=t2_name,
        theme2_volume=t2_data.get("volume", 0),
        theme2_rating=t2_data.get("average_rating", 0),
        theme2_summary=theme_summary(t2_name, t2_data),
        theme3_name=t3_name,
        theme3_volume=t3_data.get("volume", 0),
        theme3_rating=t3_data.get("average_rating", 0),
        theme3_summary=theme_summary(t3_name, t3_data),
        quote1=all_quotes[0],
        quote2=all_quotes[1],
        quote3=all_quotes[2],
        action1=actions[0],
        action2=actions[1],
        action3=actions[2],
    )
    return prompt


def draft_email_variants(insights_data: dict) -> List[Dict[str, Any]]:
    """
    Generates 3 email drafts (one-page notes) for different stakeholder roles.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not found. Generating structured drafts without AI.")
        return _generate_fallback_drafts(insights_data)

    client = Groq(api_key=api_key)
    email_drafts = []

    for role, tone in TONE_MAP.items():
        logger.info(f"Drafting one-page note for {role}...")
        prompt = _build_note_prompt(role, tone, insights_data)

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.4,
                max_tokens=1000,
            )
            body = chat_completion.choices[0].message.content
            week_date = datetime.datetime.now().strftime("%B %d, %Y")
            email_drafts.append({
                "role": role,
                "subject": f"[Kuvera Weekly Pulse] {week_date} — {role} Briefing",
                "body": body,
                "timestamp": datetime.datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to draft email for {role}: {e}")
            # Fall back to structured note without AI
            email_drafts.extend(_generate_fallback_drafts(insights_data, roles=[role]))

    return email_drafts


def _generate_fallback_drafts(insights_data: dict, roles=None) -> List[Dict[str, Any]]:
    """Generate a well-structured note without AI if Groq fails."""
    if roles is None:
        roles = list(TONE_MAP.keys())

    local_clusters = insights_data.get("local_clusters", {})
    action_ideas = insights_data.get("action_ideas", [])
    week_date = datetime.datetime.now().strftime("%B %d, %Y")

    sorted_themes = sorted(local_clusters.items(), key=lambda x: x[1].get("volume", 0), reverse=True)[:3]
    total_reviews = sum(d.get("volume", 0) for _, d in local_clusters.items())

    all_quotes = []
    for _, data in sorted_themes:
        all_quotes.extend(data.get("representative_quotes", []))
    all_quotes = [q for q in all_quotes if q and len(q.strip()) > 10][:3]
    while len(all_quotes) < 3:
        all_quotes.append("Users appreciate a smooth investment experience.")

    while len(action_ideas) < 3:
        action_ideas.append("Review and prioritize top user-reported issues.")
    actions = action_ideas[:3]

    drafts = []
    for role in roles:
        theme_section = ""
        for i, (name, data) in enumerate(sorted_themes, 1):
            theme_section += f"{i}. {name} ({data.get('volume',0)} reviews, Avg Rating: {data.get('average_rating',0)}/5)\n\n"

        body = f"""KUVERA WEEKLY PULSE NOTE
Week of {week_date} | For: {role}
{'—' * 40}

TOP 3 FEEDBACK THEMES THIS WEEK
(from {total_reviews} Google Play reviews analyzed)

{theme_section}
{'—' * 40}
3 USER VOICES THIS WEEK

"{all_quotes[0]}"

"{all_quotes[1]}"

"{all_quotes[2]}"

{'—' * 40}
3 RECOMMENDED ACTIONS

1. {actions[0]}
2. {actions[1]}
3. {actions[2]}

{'—' * 40}
Generated by Kuvera Pulse AI Engine | Confidential"""

        drafts.append({
            "role": role,
            "subject": f"[Kuvera Weekly Pulse] {week_date} — {role} Briefing",
            "body": body,
            "timestamp": datetime.datetime.now().isoformat()
        })
    return drafts


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
