import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import datetime
import logging
from config.settings import LOG_DIR, LOG_LEVEL
# FORCE RESOLVE DEPENDENCY CONFLICT ON RENDER
import subprocess
import sys
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "urllib3==1.26.15", "six"])
    print("Forced installation of urllib3==1.26.15 to fix app-store-scraper compatibility.")
except Exception as e:
    print(f"Warning: Forced pip install failed: {e}")


# Configure logging
handlers = [logging.StreamHandler()]
try:
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_DIR / "mcp_server.log")
    handlers.append(file_handler)
except Exception as e:
    print(f"Warning: Could not initialize FileHandler: {e}. Logging to console only.")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)
logger = logging.getLogger("mcp_server")

from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="Kuvera Weekly Pulse MCP Server", version="1.0.0")

# Enable CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WeeklyPulseRequest(BaseModel):
    app_name: str = "Kuvera"
    weeks: int = 8
    recipient_role: Optional[str] = None

class SendEmailRequest(BaseModel):
    role: str  # "Product Team", "Support Team", "Leadership"
    recipient_email: str
    sender_name: Optional[str] = "Kuvera Pulse AI Engine"

@app.get("/mcp/latest-results")
async def get_latest_results():
    from config.settings import OUTPUT_DIR, APP_NAME
    
    try:
        insights_path = OUTPUT_DIR / "clustered_insights.json"
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        emails_path = OUTPUT_DIR / f"{APP_NAME}_stakeholder_emails_{today_str}.json"
        
        results = {
            "insights": {},
            "emails": [],
            "last_updated": None
        }
        
        if insights_path.exists():
            with open(insights_path, 'r', encoding='utf-8') as f:
                results["insights"] = json.load(f)
                results["last_updated"] = datetime.datetime.fromtimestamp(insights_path.stat().st_mtime).isoformat()
        
        if emails_path.exists():
            with open(emails_path, 'r', encoding='utf-8') as f:
                results["emails"] = json.load(f)
                
        return results
    except Exception as e:
        logger.error(f"Error fetching latest results: {e}")
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/mcp/download-note/{filename}")
async def download_note(filename: str):
    from config.settings import OUTPUT_DIR
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not filename.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="PDF note not found. Please run the pulse first.")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/mcp/send-email")
def send_email_with_pdf(request: SendEmailRequest):
    """Gmail MCP Tool: Sends a role-specific pulse note email with PDF attached via SMTP."""
    import smtplib
    import os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from config.settings import OUTPUT_DIR

    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        raise HTTPException(status_code=500, detail="SMTP credentials not configured. Set SMTP_EMAIL and SMTP_PASSWORD in Render environment.")

    # Find the PDF for this role
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    pdf_filename = f"Kuvera_Pulse_{request.role.replace(' ', '_')}_{today_str}.pdf"
    pdf_path = OUTPUT_DIR / pdf_filename

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF note for '{request.role}' not found. Please run the pulse first.")

    week_date = datetime.datetime.now().strftime("%B %d, %Y")
    subject = f"[Kuvera Weekly Pulse] {week_date} — {request.role} Briefing"

    # Short email body
    role_intros = {
        "Product Team": "Hi team,\n\nThis week's Kuvera Pulse Note is attached. It highlights the top engineering pain points from recent Play Store reviews, along with recommended sprint items.",
        "Support Team": "Hi Support team,\n\nThis week's Kuvera Pulse Note is attached. It covers the top escalation themes and agent talking points for this week.",
        "Leadership": "Hi,\n\nThis week's Kuvera Pulse Note is attached. It summarises the most critical sentiment signals and strategic recommendations."
    }
    body_text = role_intros.get(request.role, "Please find this week's Kuvera Pulse Note attached.")
    body_text += f"\n\nThe note covers:\n  • Top 3 critical feedback themes\n  • 3 real user quotes\n  • 3 recommended actions for your team\n\nRegards,\n{request.sender_name}"

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = f"{request.sender_name} <{smtp_email}>"
    msg["To"] = request.recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))

    # Attach PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
    pdf_attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(pdf_attachment)

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, request.recipient_email, msg.as_string())
        logger.info(f"Email sent to {request.recipient_email} for role '{request.role}'")
        return {"status": "success", "message": f"Email with PDF note sent to {request.recipient_email}"}
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="Gmail authentication failed. Ensure SMTP_PASSWORD is a Gmail App Password (not your regular password). Enable 2FA and generate an App Password at myaccount.google.com/apppasswords")
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.post("/mcp/run-weekly-pulse")
def run_weekly_pulse(request: WeeklyPulseRequest):
    logger.info(f"🚀 Starting weekly pulse for {request.app_name} (Last {request.weeks} weeks)")
    
    try:
        # Lazy-load tools to ensure server starts regardless of tool-level import issues
        from tools.review_ingestion import run_ingestion_pipeline
        from tools.theme_clustering import run_clustering_pipeline
        from tools.insight_generation import run_insight_generation
        from tools.email_draft import run_email_drafting
        from tools.pdf_note import generate_all_pdf_notes
        from config.settings import OUTPUT_DIR, APP_NAME
        import json

        # Phase 2: Ingestion
        logger.info("Executing Phase 2: Ingestion...")
        run_ingestion_pipeline()
        
        # Phase 3: Clustering
        logger.info("Executing Phase 3: Clustering...")
        run_clustering_pipeline(app_name=request.app_name)
        
        # Phase 4: Report Generation (MD, PDF, HTML)
        logger.info("Executing Phase 4: Report Generation...")
        run_insight_generation()
        
        # Phase 5: Email Drafting + PDF Note Generation
        logger.info("Executing Phase 5: Email Drafting + PDF Note Generation...")
        run_email_drafting()
        
        logger.info("✅ Full Weekly Pulse Cycle Completed Successfully.")
        return {
            "status": "success",
            "message": f"Weekly pulse for {request.app_name} completed successfully.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
