import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
import logging
from config.settings import LOG_DIR, LOG_LEVEL

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


@app.post("/mcp/run-weekly-pulse")
def run_weekly_pulse(request: WeeklyPulseRequest):
    logger.info(f"🚀 Starting weekly pulse for {request.app_name} (Last {request.weeks} weeks)")
    
    try:
        # Lazy-load tools to ensure server starts regardless of tool-level import issues
        from tools.review_ingestion import run_ingestion_pipeline
        from tools.theme_clustering import run_clustering_pipeline
        from tools.insight_generation import run_insight_generation
        from tools.email_draft import run_email_drafting
        from tools.report_html import generate_report_html
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
        
        # Phase 5: Email Drafting
        logger.info("Executing Phase 5: Email Drafting...")
        run_email_drafting()

        # Phase 6: Interactive HTML Dashboard Synthesis
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        input_file = OUTPUT_DIR / "clustered_insights.json"
        emails_file = OUTPUT_DIR / f"Kuvera_stakeholder_emails_{today_str}.json"
        
        if input_file.exists() and emails_file.exists():
            with open(input_file, 'r', encoding='utf-8') as f:
                insights_data = json.load(f)
            with open(emails_file, 'r', encoding='utf-8') as f:
                email_drafts = json.load(f)
                
            html_output = OUTPUT_DIR / f"{APP_NAME}_dashboard_{today_str}.html"
            generate_report_html(insights_data, email_drafts, str(html_output))
            logger.info(f"🚀 Interactive Dashboard created: {html_output}")
        
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
