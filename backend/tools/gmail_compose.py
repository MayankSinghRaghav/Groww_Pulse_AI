"""
Gmail Compose URL Generator
Opens Gmail compose window with pre-filled content and PDF attachment link
This is the approach where user manually sends the email through Gmail UI
"""

import os
import logging
import datetime
from pathlib import Path
from urllib.parse import urlencode
from config.settings import OUTPUT_DIR

logger = logging.getLogger("gmail_compose")

def generate_gmail_compose_url(role: str, recipient_email: str = "", backend_url: str = "http://localhost:8000") -> dict:
    """
    Generate a Gmail compose URL that opens Gmail with:
    - Pre-filled subject
    - Pre-filled body
    - Link to download and attach PDF
    - Recipient email (if provided)
    
    Returns a dict with the compose URL and instructions
    """
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    week_date = datetime.datetime.now().strftime("%B %d, %Y")
    pdf_filename = f"Groww_Pulse_{role.replace(' ', '_')}_{today_str}.pdf"
    pdf_download_url = f"{backend_url}/mcp/download-note/{pdf_filename}"
    
    # Check if PDF exists
    pdf_path = OUTPUT_DIR / pdf_filename
    pdf_exists = pdf_path.exists()
    
    # Subject line
    subject = f"Weekly Groww Pulse for {role}"
    
    # Email body with PDF download link
    role_intros = {
        "Product Team": "Hi team,\n\nThis week's Groww Pulse Note highlights the top engineering pain points from recent Play Store reviews, along with recommended sprint items.",
        "Support Team": "Hi Support team,\n\nThis week's Groww Pulse Note covers the top escalation themes and agent talking points for this week.",
        "Leadership": "Hi,\n\nThis week's Groww Pulse Note summarises the most critical sentiment signals and strategic recommendations."
    }
    
    body_intro = role_intros.get(role, "Please find this week's Groww Pulse Note attached.")
    
    # Create body text
    if pdf_exists:
        body = f"""{body_intro}

Please find the detailed weekly briefing in the attached document.

This note covers:
  • Top 3 critical user-feedback themes
  • 3 real user quotes
  • One high-impact strategic recommendation

Regards,
Groww Pulse AI Engine
(Automated weekly digest — Groww)"""
    else:
        body = f"""{body_intro}

⚠️ PDF Note Not Found. Please generate the pulse first.

---
Regards,
Groww Pulse AI Engine"""
    
    # Generate Gmail compose URL
    # Using 'su' for subject as it is the standard for Gmail compose view (view=cm)
    compose_params = {
        'to': recipient_email,
        'su': subject,
        'body': body
    }
    
    # Filter out empty parameters
    compose_params = {k: v for k, v in compose_params.items() if v}
    
    gmail_compose_url = f"https://mail.google.com/mail/?view=cm&{urlencode(compose_params)}"
    
    return {
        "status": "success",
        "role": role,
        "pdf_exists": pdf_exists,
        "pdf_filename": pdf_filename,
        "pdf_download_url": pdf_download_url,
        "gmail_compose_url": gmail_compose_url,
        "recipient_email": recipient_email,
        "subject": subject,
        "body": body,
        "instructions": {
            "step1": "Click the Gmail compose URL to open Gmail",
            "step2": "Download the PDF from the link provided in the email body",
            "step3": "Attach the PDF to the email manually (drag & drop or use attachment button)",
            "step4": "Enter recipient email address if not pre-filled",
            "step5": "Review the email and click Send"
        }
    }


def open_gmail_compose(role: str, recipient_email: str = "", backend_url: str = "http://localhost:8000") -> str:
    """
    Generate and return the Gmail compose URL
    This can be used to redirect users to Gmail
    """
    result = generate_gmail_compose_url(role, recipient_email, backend_url)
    return result["gmail_compose_url"]


if __name__ == "__main__":
    # Test the compose URL generation
    logging.basicConfig(level=logging.INFO)
    
    print("=== Gmail Compose URL Generator Test ===\n")
    
    # Test with Product Team
    result = generate_gmail_compose_url("Product Team", "test@example.com")
    
    print(f"Role: {result['role']}")
    print(f"PDF Exists: {result['pdf_exists']}")
    print(f"PDF Download URL: {result['pdf_download_url']}")
    print(f"\nGmail Compose URL:")
    print(result['gmail_compose_url'])
    print(f"\nInstructions:")
    for step, desc in result['instructions'].items():
        print(f"  {step}: {desc}")
