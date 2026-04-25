import json
import logging
import datetime
import os
from groq import Groq
from typing import List, Dict, Any
from config.settings import OUTPUT_DIR, APP_NAME, MODEL_NAME
from config.prompts import TONE_MAP

logger = logging.getLogger("email_draft")

# Role-specific instructions for what each audience cares about
ROLE_CONTEXT = {
    "Product Team": {
        "focus": "technical root causes, sprint priorities, and bug fixes",
        "what_they_need": "specific feature areas to investigate, prioritized by severity and volume, with reproduction steps or patterns from user quotes",
        "format_hint": "Use bullet points for action items. Be precise about which screen/flow is broken. Suggest sprint backlog items."
    },
    "Support Team": {
        "focus": "how to handle user escalations and common complaints this week",
        "what_they_need": "scripts or talking points for the top complaints, so agents can empathize and respond correctly when users call in",
        "format_hint": "Use a warm, empathetic tone. Provide 2-3 agent talking points per theme. Focus on user frustration patterns."
    },
    "Leadership": {
        "focus": "business impact, retention risk, and strategic decisions needed",
        "what_they_need": "a high-level view of user sentiment health, which themes pose the biggest retention risk, and what one strategic decision would move the needle",
        "format_hint": "Be concise and executive. No jargon. Use % or numbers where possible. End with a single recommended strategic priority."
    }
}


def _build_role_specific_prompt(role: str, tone: str, insights_data: dict) -> str:
    """Build a role-specific prompt that yields genuinely different emails."""
    local_clusters = insights_data.get("local_clusters", {})
    action_ideas = insights_data.get("action_ideas", [])
    week_date = datetime.datetime.now().strftime("%B %d, %Y")

    # Sort by volume and take top 3
    sorted_themes = sorted(local_clusters.items(), key=lambda x: x[1].get("volume", 0), reverse=True)[:3]
    total_reviews = sum(d.get("volume", 0) for _, d in local_clusters.items())

    # Build raw data block for the AI
    themes_block = ""
    all_quotes = []
    for name, data in sorted_themes:
        themes_block += f"\n• {name}: {data.get('volume', 0)} reviews, avg rating {data.get('average_rating', 0)}/5\n"
        quotes = data.get("representative_quotes", [])
        if quotes:
            themes_block += f"  Sample quotes: {' | '.join(quotes[:2])}\n"
            all_quotes.extend(quotes[:2])

    while len(action_ideas) < 3:
        action_ideas.append("Review top-reported issues in the next sprint.")
    actions_block = "\n".join([f"{i+1}. {a}" for i, a in enumerate(action_ideas[:3])])

    ctx = ROLE_CONTEXT[role]

    prompt = f"""You are a Product Communications Lead at Kuvera by CRED.
Write a weekly pulse briefing email for the {role} audience. Tone: {tone}.

YOUR AUDIENCE CARES ABOUT: {ctx['focus']}
WHAT THEY NEED FROM THIS EMAIL: {ctx['what_they_need']}
FORMAT GUIDANCE: {ctx['format_hint']}

--- RAW DATA (Week of {week_date}) ---
Total reviews analyzed: {total_reviews} (Google Play)
Top 3 themes this week:
{themes_block}
Suggested action ideas:
{actions_block}

--- YOUR TASK ---
Write the complete email body (no placeholder text). 
Start with: "Subject: [Kuvera Weekly Pulse] {week_date} — {role} Briefing"
Then write the email body tailored specifically for the {role}.
Include exactly:
- Top 3 themes reframed for this audience's perspective
- 3 real user quotes (pick the most relevant ones for this audience)
- 3 action items written specifically for what THIS team can do
End with: "— Kuvera Pulse AI Engine"
"""
    return prompt


def _generate_fallback_drafts(insights_data: dict, roles: list = None) -> List[Dict[str, Any]]:
    """Fallback: structured notes without AI when Groq is unavailable."""
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

    role_openers = {
        "Product Team": f"Hi team,\n\nThis week's review data flags {sorted_themes[0][0] if sorted_themes else 'key areas'} as the highest-priority engineering concern. Here's what needs to go into the backlog:",
        "Support Team": f"Hi Support team,\n\nHere are the top themes users are calling in about this week. Use these talking points when handling escalations:",
        "Leadership": f"Hi,\n\nThis week's Kuvera app reviews ({total_reviews} analyzed) show the following strategic signals worth your attention:"
    }

    drafts = []
    for role in roles:
        theme_lines = ""
        for i, (name, data) in enumerate(sorted_themes, 1):
            theme_lines += f"{i}. {name} — {data.get('volume', 0)} reviews, Avg: {data.get('average_rating', 0)}/5\n"

        body = f"""Subject: [Kuvera Weekly Pulse] {week_date} — {role} Briefing

{role_openers.get(role, 'Hi,')}

TOP 3 THEMES
{theme_lines}
USER VOICES
• "{all_quotes[0]}"
• "{all_quotes[1]}"
• "{all_quotes[2]}"

ACTIONS FOR {role.upper()}
1. {action_ideas[0]}
2. {action_ideas[1]}
3. {action_ideas[2]}

— Kuvera Pulse AI Engine"""

        drafts.append({
            "role": role,
            "subject": f"[Kuvera Weekly Pulse] {week_date} — {role} Briefing",
            "body": body,
            "timestamp": datetime.datetime.now().isoformat()
        })
    return drafts


def draft_email_variants(insights_data: dict) -> List[Dict[str, Any]]:
    """Generates 3 role-specific email drafts using Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not found. Using fallback structured drafts.")
        return _generate_fallback_drafts(insights_data)

    client = Groq(api_key=api_key)
    email_drafts = []

    for role, tone in TONE_MAP.items():
        logger.info(f"Drafting role-specific note for {role}...")
        prompt = _build_role_specific_prompt(role, tone, insights_data)

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.6,
                max_tokens=1200,
            )
            week_date = datetime.datetime.now().strftime("%B %d, %Y")
            email_drafts.append({
                "role": role,
                "subject": f"[Kuvera Weekly Pulse] {week_date} — {role} Briefing",
                "body": chat_completion.choices[0].message.content,
                "timestamp": datetime.datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to draft email for {role}: {e}")
            email_drafts.extend(_generate_fallback_drafts(insights_data, roles=[role]))

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
