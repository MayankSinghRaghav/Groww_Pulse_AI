import json
import logging
import datetime
import os
from config.settings import OUTPUT_DIR, APP_NAME
from jinja2 import Template
from fpdf import FPDF

logger = logging.getLogger("insight_generation")

MARKDOWN_TEMPLATE = """
# {{ app_name }} — Weekly One-Page Note 📝

**Generated on:** {{ date }}

## 🎯 Top 3 Themes
{% for theme, data in top_3_themes %}
### {{ loop.index }}. {{ theme }}
- **Volume:** {{ data.volume }} reviews | **Rating:** {{ data.average_rating }} / 5.0
- **Voice of the Customer:**
  {% for quote in data.representative_quotes[:3] %}
  > "{{ quote }}"
  {% endfor %}

{% endfor %}

---

## ⚡ Action Ideas
{% for idea in action_ideas %}
- {{ idea }}
{% endfor %}

---
*AI-extracted from latest App Store & Google Play feedback.*
"""

def generate_markdown(insights_data: dict, output_path: str) -> str:
    """Renders the insights data into a structured Weekly Note."""
    try:
        template = Template(MARKDOWN_TEMPLATE)
        
        # Sort and take top 3 themes
        sorted_themes = sorted(insights_data.get("local_clusters", {}).items(), 
                               key=lambda x: x[1]['volume'], reverse=True)[:3]
        
        rendered_md = template.render(
            app_name=APP_NAME,
            date=datetime.datetime.now().strftime("%B %d, %Y"),
            top_3_themes=sorted_themes,
            action_ideas=insights_data.get("action_ideas", [])
        )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_md)
            
        logger.info(f"Weekly One-Page Note generated: {output_path}")
        return rendered_md
    except Exception as e:
        logger.error(f"Failed to generate Markdown: {e}")
        return ""

def generate_pdf(markdown_text: str, output_path: str):
    """Converts the Markdown report to a branded Kuvera PDF using a stream-based approach."""
    try:
        # Sanitize for latin-1
        clean_text = markdown_text.encode('latin-1', 'replace').decode('latin-1')
        clean_text = clean_text.replace('\r', '')
        
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        # Simple Header using write()
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(0, 0, 0)
        pdf.write(15, "KUVERA")
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.write(15, " BY CRED")
        pdf.ln(15)
        
        # Content (Pure flow)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.write(7, clean_text)
        
        # Ensure fresh write
        if os.path.exists(output_path):
            os.remove(output_path)
            
        pdf.output(output_path)
        logger.info(f"Report generated: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")

def run_insight_generation():
    logger.info("Starting insight generation phase.")
    
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

    today_str = datetime.datetime.now().strftime("%Y%m%d")
    md_output_path = OUTPUT_DIR / f"{APP_NAME}_weekly_pulse_{today_str}.md"
    pdf_output_path = OUTPUT_DIR / f"{APP_NAME}_weekly_pulse_{today_str}.pdf"
    
    # Generate Markdown
    rendered_md = generate_markdown(insights_data, str(md_output_path))
    
    # Generate PDF
    if rendered_md:
        generate_pdf(rendered_md, str(pdf_output_path))
        
    logger.info("Insight generation pipeline complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_insight_generation()
