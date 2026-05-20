import os
import sys
import datetime

# Ensure backend imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.review_ingestion import run_ingestion_pipeline
from tools.theme_clustering import run_clustering_pipeline
from tools.insight_generation import run_insight_generation
from tools.email_draft import run_email_drafting

if __name__ == "__main__":
    print(f"=== Groww Pulsator pipeline triggered: {datetime.datetime.now().isoformat()} ===")
    try:
        print("1/4 Scrape App Store & Google Play reviews...")
        run_ingestion_pipeline()
        
        print("2/4 Perform advanced LLM categorization & theme clustering...")
        run_clustering_pipeline(app_name="Groww")
        
        print("3/4 Generate PDF Stakeholder action notes...")
        run_insight_generation()
        
        print("4/4 Draft emails briefings...")
        run_email_drafting()
        
        print("=== Groww Pulsator Ingestion Pipeline Succeeded! ===")
    except Exception as e:
        print(f"=== Pipeline Failed: {e} ===", file=sys.stderr)
        sys.exit(1)
