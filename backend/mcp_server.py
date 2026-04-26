import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
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
from fastapi.responses import RedirectResponse
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

# ==================== OAuth 2.0 Endpoints ====================

@app.get("/oauth/authorize")
async def oauth_authorize():
    """
    Step 1: Initiate OAuth flow - redirect user to Google consent screen
    """
    try:
        from tools.gmail_oauth import get_authorization_url
        auth_url = get_authorization_url()
        logger.info("Redirecting to Google OAuth consent screen")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth authorization error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")

@app.get("/oauth/callback")
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """
    Step 2: Handle OAuth callback from Google
    Exchange authorization code for access/refresh tokens
    """
    if error:
        logger.error(f"OAuth error: {error}")
        return {
            "status": "error",
            "message": f"Authorization failed: {error}",
            "details": "User denied access or an error occurred during authorization"
        }
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state parameter")
    
    try:
        from tools.gmail_oauth import handle_oauth_callback, get_user_profile
        from urllib.parse import urlencode
        
        # Reconstruct the full callback URL for token exchange
        authorization_response = f"{request.url.scheme}://{request.url.netloc}{request.url.path}?{urlencode({'code': code, 'state': state})}"
        
        # Exchange code for tokens
        creds = handle_oauth_callback(authorization_response, state)
        
        # Get user profile
        profile = get_user_profile(creds)
        
        logger.info(f"OAuth successful! Authenticated as: {profile['email']}")
        
        return {
            "status": "success",
            "message": "OAuth authorization completed successfully!",
            "user": {
                "email": profile['email'],
                "messages_total": profile['messages_total']
            },
            "next_steps": "You can now use the /mcp/send-email endpoint to send emails via Gmail API"
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@app.get("/oauth/status")
async def oauth_status():
    """Check current OAuth authentication status"""
    try:
        from tools.gmail_oauth import refresh_credentials_if_needed, get_user_profile
        
        creds = refresh_credentials_if_needed()
        
        if not creds:
            return {
                "authenticated": False,
                "message": "No valid OAuth credentials found. Please authorize first via /oauth/authorize"
            }
        
        profile = get_user_profile(creds)
        
        return {
            "authenticated": True,
            "user": {
                "email": profile['email'],
                "messages_total": profile['messages_total']
            },
            "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
            "message": "OAuth credentials are valid and ready to use"
        }
        
    except Exception as e:
        logger.error(f"OAuth status check error: {e}")
        return {
            "authenticated": False,
            "error": str(e)
        }

@app.post("/oauth/logout")
async def oauth_logout():
    """Revoke OAuth credentials (logout)"""
    try:
        from tools.gmail_oauth import get_stored_credentials, revoke_credentials
        
        creds = get_stored_credentials()
        
        if not creds:
            return {
                "status": "success",
                "message": "No credentials to revoke"
            }
        
        success = revoke_credentials(creds)
        
        if success:
            return {
                "status": "success",
                "message": "OAuth credentials revoked successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to revoke credentials")
            
    except Exception as e:
        logger.error(f"OAuth logout error: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.post("/oauth/test-email")
async def test_oauth_email():
    """Send a test email using OAuth to verify the integration works"""
    try:
        from tools.gmail_oauth import refresh_credentials_if_needed, get_user_profile, send_email_via_gmail_api
        
        # Get valid credentials
        creds = refresh_credentials_if_needed()
        
        if not creds:
            raise HTTPException(
                status_code=401, 
                detail="No valid OAuth credentials. Please authorize first via /oauth/authorize"
            )
        
        # Get user profile
        profile = get_user_profile(creds)
        sender_email = profile['email']
        
        # Send test email to self
        subject = "[Kuvera Pulse] OAuth Test Email"
        body_text = """This is a test email to verify that the Gmail OAuth integration is working correctly.

If you received this email, the OAuth 2.0 authentication is properly configured!

Next steps:
1. Run the weekly pulse to generate reports
2. Use the /mcp/send-email endpoint to send stakeholder emails with PDF attachments

Regards,
Kuvera Pulse AI Engine"""
        
        result = send_email_via_gmail_api(
            creds=creds,
            sender=f"Kuvera Pulse <{sender_email}>",
            to=sender_email,
            subject=subject,
            body_text=body_text
        )
        
        return {
            "status": "success",
            "message": f"Test email sent to {sender_email}",
            "message_id": result['message_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test email error: {e}")
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")

@app.get("/mcp/gmail-compose")
async def gmail_compose_url(role: str, recipient_email: str = "", request: Request = None):
    """
    Generate Gmail compose URL with pre-filled content
    Opens Gmail compose window with subject, body, and PDF download link
    User manually attaches PDF and sends
    """
    try:
        from tools.gmail_compose import generate_gmail_compose_url
        import os
        
        # Get backend URL from environment or use default
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        # For production, use the actual backend URL
        if request and hasattr(request, 'base_url') and "onrender.com" in str(request.base_url):
            backend_url = str(request.base_url).rstrip('/')
        
        result = generate_gmail_compose_url(role, recipient_email, backend_url)
        
        logger.info(f"Generated Gmail compose URL for role: {role}")
        return result
        
    except Exception as e:
        logger.error(f"Gmail compose URL generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate compose URL: {str(e)}")

# ==================== Existing Endpoints ====================

@app.get("/mcp/download-note/{filename}")
async def download_note(filename: str):
    from config.settings import OUTPUT_DIR
    import os
    
    file_path = OUTPUT_DIR / filename
    
    # If PDF doesn't exist, try to generate it on-demand
    if not file_path.exists():
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=404, detail="Invalid file type. Only PDF files are allowed.")
        
        try:
            logger.info(f"PDF not found: {filename}, attempting on-demand generation...")
            
            # Load insights
            insights_path = OUTPUT_DIR / "clustered_insights.json"
            if not insights_path.exists():
                raise HTTPException(status_code=404, detail="No insights data found. Please run the pulse first.")
            
            import json
            with open(insights_path, 'r', encoding='utf-8') as f:
                insights = json.load(f)
            
            # Extract role from filename
            # Format: Kuvera_Pulse_Product_Team_20260426.pdf
            parts = filename.replace('.pdf', '').split('_')
            if len(parts) >= 4:
                role_parts = parts[2:-1]  # Get everything between "Pulse" and the date
                role = ' '.join(role_parts)
                
                # Generate PDF
                from tools.pdf_note import generate_pdf_note
                action_ideas = insights.get("action_ideas", [])
                if isinstance(action_ideas, str):
                    action_ideas = [action_ideas]
                
                # Generate PDF to the expected output path
                generate_pdf_note(role, insights, action_ideas, str(file_path))
                logger.info(f"Generated PDF on-demand: {filename}")
                
                # Check if it exists now
                if file_path.exists():
                    return FileResponse(
                        path=str(file_path),
                        media_type="application/pdf",
                        filename=filename,
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"PDF generation failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"On-demand PDF generation failed: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=error_detail)
        
        raise HTTPException(status_code=404, detail="PDF note not found. Please run the pulse first.")
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/mcp/send-email")
def send_email_with_pdf(request: SendEmailRequest):
    """
    Gmail MCP Tool: Sends a role-specific pulse note email with PDF attached.
    Uses OAuth 2.0 for secure authentication (fallback to SMTP if OAuth not configured)
    """
    from config.settings import OUTPUT_DIR
    import os

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

    # Try OAuth first, fallback to SMTP
    try:
        from tools.gmail_oauth import send_email_with_oauth, refresh_credentials_if_needed
        
        # Check if OAuth is configured
        creds = refresh_credentials_if_needed()
        
        if creds:
            # Use OAuth
            logger.info(f"Sending email via Gmail OAuth to {request.recipient_email}")
            result = send_email_with_oauth(
                to=request.recipient_email,
                subject=subject,
                body_text=body_text,
                pdf_path=str(pdf_path),
                sender_name=request.sender_name
            )
            
            if result['status'] == 'success':
                logger.info(f"Email sent successfully to {request.recipient_email} via OAuth. Message ID: {result.get('message_id')}")
                return {
                    "status": "success",
                    "message": f"Email with PDF note sent to {request.recipient_email} via Gmail API",
                    "method": "oauth",
                    "message_id": result.get('message_id')
                }
            else:
                logger.warning(f"OAuth send failed: {result.get('message')}. Falling back to SMTP...")
        else:
            logger.info("No OAuth credentials found, using SMTP fallback")
            
    except Exception as e:
        logger.warning(f"OAuth error: {e}. Falling back to SMTP...")
    
    # Fallback to SMTP
    logger.info(f"Sending email via SMTP to {request.recipient_email}")
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        raise HTTPException(
            status_code=500, 
            detail="Neither OAuth nor SMTP credentials are configured. Please either:\n1. Complete OAuth authorization via /oauth/authorize, OR\n2. Set SMTP_EMAIL and SMTP_PASSWORD in environment variables"
        )

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
        logger.info(f"Email sent to {request.recipient_email} for role '{request.role}' via SMTP")
        return {
            "status": "success", 
            "message": f"Email with PDF note sent to {request.recipient_email} via SMTP",
            "method": "smtp"
        }
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=401, 
            detail="Gmail authentication failed. Ensure SMTP_PASSWORD is a Gmail App Password (not your regular password). Enable 2FA and generate an App Password at myaccount.google.com/apppasswords"
        )
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
