import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
import logging
import os
import json
import glob
from pathlib import Path
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

# ==================== Results Endpoints ====================

@app.get("/mcp/latest-results")
async def get_latest_results():
    from config.settings import OUTPUT_DIR, APP_NAME
    import glob
    
    try:
        insights_path = OUTPUT_DIR / "clustered_insights.json"
        
        results = {
            "insights": {},
            "emails": [],
            "last_updated": None
        }
        
        if insights_path.exists():
            with open(insights_path, 'r', encoding='utf-8') as f:
                results["insights"] = json.load(f)
                results["last_updated"] = datetime.datetime.fromtimestamp(insights_path.stat().st_mtime).isoformat()
        
        # Find the MOST RECENT stakeholder emails file
        email_files = sorted(
            glob.glob(str(OUTPUT_DIR / f"{APP_NAME}_stakeholder_emails_*.json")),
            key=lambda f: os.path.getmtime(f),
            reverse=True
        )
        
        emails_loaded = False
        for email_file in email_files:
            try:
                with open(email_file, 'r', encoding='utf-8') as f:
                    emails_data = json.load(f)
                    if emails_data and len(emails_data) > 0:
                        import os as _os
                        backend_url = _os.getenv("BACKEND_URL", "https://kuvera-pulse.onrender.com")
                        today_str = datetime.datetime.now().strftime("%Y%m%d")
                        for draft in emails_data:
                            role = draft.get("role", "Leadership")
                            pdf_fn = f"Kuvera_Pulse_{role.replace(' ', '_')}_{today_str}.pdf"
                            draft["download_link"] = f"{backend_url}/mcp/download-note/{pdf_fn}"
                            draft["pdf_filename"] = pdf_fn
                        results["emails"] = emails_data
                        emails_loaded = True
                        break
            except Exception as e:
                continue
        
        return results
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.datetime.now().isoformat()}

# ==================== OAuth 2.0 Endpoints ====================

@app.get("/oauth/authorize")
async def oauth_authorize():
    try:
        from tools.gmail_oauth import get_authorization_url
        auth_url = get_authorization_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth authorize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/callback")
async def oauth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    if error:
        return RedirectResponse(f"{os.getenv('FRONTEND_URL', 'https://kuvera-pulse.vercel.app')}?auth=error&msg={error}")
    
    try:
        from tools.gmail_oauth import handle_oauth_callback
        # Gmail API requires exact redirect URI match
        authorization_response = str(request.url)
        handle_oauth_callback(authorization_response, state)
        
        frontend_url = os.getenv("FRONTEND_URL", "https://kuvera-pulse.vercel.app")
        return RedirectResponse(f"{frontend_url}?auth=success")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/status")
async def oauth_status():
    try:
        from tools.gmail_oauth import refresh_credentials_if_needed, get_user_profile
        creds = refresh_credentials_if_needed()
        if not creds:
            return {"authenticated": False}
        
        profile = get_user_profile(creds)
        return {
            "authenticated": True,
            "email": profile.get('email'),
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }
    except Exception as e:
        return {"authenticated": False, "error": str(e)}

@app.post("/oauth/logout")
async def oauth_logout():
    try:
        from tools.gmail_oauth import get_stored_credentials, revoke_credentials
        creds = get_stored_credentials()
        if creds:
            revoke_credentials(creds)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== Gmail Draft Integration ====================

@app.get("/mcp/create-gmail-draft")
async def create_gmail_draft(role: str, recipient_email: str = ""):
    """Creates a Gmail draft with the PDF attached via Gmail API (OAuth)"""
    try:
        from tools.gmail_oauth import create_draft_via_oauth
        from tools.gmail_compose import generate_gmail_compose_url
        from config.settings import OUTPUT_DIR
        
        _ensure_pdf_exists(role)
        
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        pdf_filename = f"Kuvera_Pulse_{role.replace(' ', '_')}_{today_str}.pdf"
        pdf_path = OUTPUT_DIR / pdf_filename
        
        backend_url = os.getenv("BACKEND_URL", "https://kuvera-pulse.onrender.com")
        compose_data = generate_gmail_compose_url(role, recipient_email, backend_url)
        
        result = create_draft_via_oauth(
            to=recipient_email,
            subject=compose_data['su'],
            body_text=compose_data['body'],
            pdf_path=str(pdf_path)
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "draft_id": result['draft_id'],
                "gmail_url": "https://mail.google.com/mail/u/0/#drafts"
            }
        elif result['status'] == 'unauthorized':
            return {
                "status": "unauthorized",
                "auth_url": f"{backend_url}/oauth/authorize"
            }
        else:
            return result
    except Exception as e:
        logger.error(f"Draft creation error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/mcp/gmail-compose")
async def gmail_compose_endpoint(role: str, recipient_email: str = "", request: Request = None):
    """Legacy compose URL method (for manual attachment)"""
    from tools.gmail_compose import generate_gmail_compose_url
    backend_url = os.getenv("BACKEND_URL", "https://kuvera-pulse.onrender.com")
    _ensure_pdf_exists(role)
    return generate_gmail_compose_url(role, recipient_email, backend_url)

# ==================== PDF & Pulse Helpers ====================

def _ensure_pdf_exists(role: str) -> bool:
    from config.settings import OUTPUT_DIR
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    pdf_filename = f"Kuvera_Pulse_{role.replace(' ', '_')}_{today_str}.pdf"
    file_path = OUTPUT_DIR / pdf_filename
    
    if file_path.exists() and file_path.stat().st_size > 2048:
        return True
    
    try:
        insights_path = OUTPUT_DIR / "clustered_insights.json"
        if not insights_path.exists(): return False
        
        with open(insights_path, 'r', encoding='utf-8') as f:
            insights = json.load(f)
        
        from tools.pdf_note import generate_pdf_note
        action_ideas = insights.get("action_ideas", {})
        
        success = generate_pdf_note(role, insights, action_ideas, str(file_path))
        return success and file_path.exists()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False

@app.get("/mcp/download-note/{filename}")
async def download_note(filename: str):
    from config.settings import OUTPUT_DIR
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@app.post("/mcp/run-weekly-pulse")
def run_weekly_pulse(request: WeeklyPulseRequest):
    try:
        from tools.review_ingestion import run_ingestion_pipeline
        from tools.theme_clustering import run_clustering_pipeline
        from tools.insight_generation import run_insight_generation
        from tools.email_draft import run_email_drafting
        from config.settings import OUTPUT_DIR
        
        # Cleanup
        old_pdfs = glob.glob(str(OUTPUT_DIR / "*.pdf"))
        for p in old_pdfs: 
            try: os.remove(p)
            except: pass
            
        run_ingestion_pipeline()
        run_clustering_pipeline(app_name=request.app_name)
        run_insight_generation()
        run_email_drafting()
        
        return {"status": "success", "timestamp": datetime.datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Pulse failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/download-word/{filename}")
async def download_word(filename: str):
    from config.settings import OUTPUT_DIR
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
