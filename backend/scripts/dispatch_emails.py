import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

# Initialize paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
load_dotenv(BASE_DIR / ".env")

def send_test_emails(target_email):
    # Load credentials from environment
    sender = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    
    if not sender or not password:
        print("[ERROR] SMTP_EMAIL and SMTP_PASSWORD not found in .env")
        return

    # Load latest drafts
    drafts_file = OUTPUT_DIR / "Kuvera_stakeholder_emails_20260425.json"
    
    if not drafts_file.exists():
        print(f"[ERROR] Drafts file not found at {drafts_file}")
        return

    with open(drafts_file, 'r', encoding='utf-8') as f:
        drafts = json.load(f)

    # Setup Server
    try:
        print(f"[INFO] Connecting to SMTP server for {sender}...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        
        for draft in drafts:
            msg = MIMEMultipart()
            msg['From'] = f"Kuvera Intelligence Agent <{sender}>"
            msg['To'] = target_email
            msg['Subject'] = draft['subject']
            
            body = draft['body'] + "\n\n---\nSent by Kuvera Weekly Pulse AI Assistant"
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            print(f"[SUCCESS] Sent: {draft['role']} draft to {target_email}")
            
        server.quit()
        print("\nAll test emails dispatched successfully!")
    except Exception as e:
        print(f"[ERROR] Dispatch failed: {e}")
        print("\nTIP: If using Gmail, ensure you are using an 'App Password', not your main account password.")

if __name__ == "__main__":
    send_test_emails("riteshpatel907@gmail.com")
