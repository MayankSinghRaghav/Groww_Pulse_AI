# Kuvera Weekly Pulse Agent 🚀

An automated, zero-cost pipeline for scraping, analyzing, and reporting app store reviews using local clustering and Groq's Llama 3.3.

## 📦 Deliverables
- **Latest Report:** [Kuvera_weekly_pulse_20260425.pdf](data/outputs/Kuvera_weekly_pulse_20260425.pdf) / [HTML Dashboard](data/outputs/Kuvera_dashboard_20260425.html)
- **Stakeholder Emails:** [Kuvera_stakeholder_emails_20260425.json](data/outputs/Kuvera_stakeholder_emails_20260425.json)
- **Data Source:** [clean_reviews_20260425.csv](data/processed/clean_reviews_20260425.csv)

## 🔄 How to Re-run for a New Week
1. **Ensure Environment is Ready:**
   - Put your `GROQ_API_KEY` in the `.env` file.
2. **Launch the Service (Optional):**
   ```bash
   python mcp_server.py
   ```
3. **Execute the Pipeline:**
   ```bash
   python scripts/run_weekly_pulse.py
   ```
   *This will automatically scrape the latest reviews, cluster them, generate the branded reports (PDF/HTML/MD), and draft stakeholder emails.*

## 🏷️ Theme Legend (Taxonomy)
The system uses a two-pass classification system:

### 1. Local Keyword Themes (Deterministic)
- **Login/Auth:** Issues with PIN, Biometrics, or logging in.
- **Investment Flow:** Errors while buying/selling funds.
- **UI/UX:** Feedback on navigation, dark mode, or design.
- **Performance:** Lag, crashes, or battery drain.
- **Customer Support:** Mentions of ticket delays or help quality.
- **Onboarding/KYC:** Document upload issues or approval delays.

### 2. AI Advanced Insights (Dynamic)
Any reviews that don't match the above keywords are processed by **Llama 3.3 70B** to extract emerging themes like:
- Feature requests (e.g., "Add US Stocks").
- Specific bug reports not covered by keywords.
- Competitive comparisons.

## 🛠️ Tech Stack
- **Ingestion:** `google-play-scraper`, `app-store-scraper`
- **Analysis:** `Groq SDK` (Llama 3.3 70B)
- **Reporting:** `Jinja2`, `fpdf2`
- **Dashboard:** Vanilla HTML/CSS (Glassmorphism)
- **Automation:** FastAPI (MCP Server)

---
*Developed for Kuvera by Antigravity AI.*
