# Kuvera App Review Agent — Implementation Plan

This document outlines the structured implementation plan for the **Kuvera App Review Agent**, designed to analyze App Store and Google Play reviews weekly. The focus is to build a robust, scalable, and automated system tailored for the **Kuvera** platform, delivering valuable insights to product, support, and leadership teams.

---

## 🏗️ Guiding Architecture Overview
The system follows an MCP (Model Context Protocol) architecture featuring:
1. **Trigger:** Weekly cron job (Mondays 9:00 AM).
2. **MCP Server:** FastAPI orchestrator for handling tasks.
3. **Tools Interface:** Modular tools handling ingestion, clustering, report generation, and email drafting.
4. **LLM Engine:** Open-source models (e.g., Llama 3 8B/70B) accessed via free-tier APIs (Groq, Together AI, or local Ollama) for zero-cost operation.
5. **Output Generation:** Markdown, PDF, and JSON insights tailored for different Kuvera stakeholders.

---

## 🛠️ Phase-by-Phase Implementation Plan

### Phase 1: Project Setup & MCP Architecture
**Description:** 
Establish the foundational structure of the application. This involves creating the necessary directories (`tools/`, `config/`, `data/`, etc.), setting up the virtual environment, installing dependencies (`requirements.txt`), and defining core configuration settings including environment variables.

**Evaluation Criteria:**
- Directory structure aligns with the documented architecture.
- All Python dependencies (`fastapi`, `weasyprint`, `langchain`, `groq`, etc.) resolve and install cleanly.
- Configurations (`.env` file) can securely store and retrieve keys for free-tier services (e.g., `GROQ_API_KEY`) or local endpoints (Ollama).

**Edge Cases:**
- Missing system dependencies for `weasyprint` (e.g., Cairo/Pango).
- Conflicting Python dependency versions.
- Insufficient permissions to create the log or data directories.

---

### Phase 2: Review Ingestion Tool
**Description:** 
Implement Tool 1 (`tools/review_ingestion.py`) to systematically scrape and retrieve Kuvera app reviews from the Google Play Store and Apple App Store. It should support deduplication, date filtering (e.g., last 8 weeks), and fallback to CSV upload.

**Evaluation Criteria:**
- Successfully fetches a target volume of 500–1000 unique reviews for Kuvera.
- Reviews parse standard properties: rating, text, date, and platform source.
- Invalid or bot-like reviews are scrubbed out.

**Edge Cases:**
- Store API layout changes or blocking via CAPTCHA.
- Rate limits encountered due to aggressive scraping.
- Empty result sets returning if Kuvera has zero reviews within the filtered timeframe.

---

### Phase 3: Theme Clustering & LLM Analysis
**Description:** 
Implement Tool 2 (`tools/theme_clustering.py`). This phase aggressively minimizes LLM calls using **Hard Keyword Pre-Clustering** (matching strings locally to bypass AI) and **LLM Batch Processing** (sending 30-50 reviews per prompt). The remaining ambiguous data goes to Llama 3 (via Groq/Local) to finalize 5-7 core themes, sentiment counts, and representative quotes.

**Evaluation Criteria:**
- Accurately tags reviews with themes fitting Kuvera users (e.g., *Performance & Stability, Customer Support, UX & Navigation*, etc.).
- Cost remains at an absolute **$0.00** per run by utilizing free tiers (like Groq) or local inference.
- Output JSON contains valid sentiment counts and verbatim quotes.

**Edge Cases:**
- Llama/Open-source LLM hallucinations producing nonsensical or fabricated "representative quotes".
- Rate limit errors (`HTTP 429`) specifically hit on free-tiers API quotas (requiring robust batching/exponential backoff).
- Non-English or gibberish text in reviews misclassified as critical bugs.

---

### Phase 4: Weekly Report Generation
**Description:** 
Implement Tool 3 (`tools/insight_generation.py`) to translate the clustered LLM data into digestible narrative reports. Generates a Markdown file, converts it into a visually appealing PDF using `weasyprint`, and stores a structured JSON file in `data/outputs/`.

**Evaluation Criteria:**
- Generates `Kuvera_weekly_pulse_[DATE].md` and `Kuvera_weekly_pulse_[DATE].pdf`.
- Report highlights the aggregate metrics (e.g., overall rating) alongside top themes and prioritized recommendations.

**Edge Cases:**
- Formatting/Layout breaking when a text block or quote is unusually long in PDF generation.
- Missing fonts resulting in unreadable PDFs.
- Division by zero errors if calculating aggregate sentiment for an empty week.

---

### Phase 5: Email Draft Creation
**Description:** 
Implement Tool 4 (`tools/email_draft.py`) to craft context-aware email templates tailored to three distinct Kuvera stakeholder groups:
1. **Product Team:** Focus on features, UX, and technical roadmap impact.
2. **Support Team:** Focus on common complaints and SLAs.
3. **Leadership:** Focus on strategic health metrics and brand risks.

**Evaluation Criteria:**
- Generates 3 unique JSON payloads containing the recipient role, a customized subject line, and HTML/Plain text bodies.
- Content correctly references the week's specific insights and the PDF attachment.

**Edge Cases:**
- A theme dominated entirely by bugs creating an empty "Features" section for the product template.
- Invalid HTML structure rendering emails badly in traditional clients (e.g., Outlook).

---

### Phase 6: MCP Server & Agent Orchestration
**Description:** 
Wire all 4 modular tools through a FastAPI instance (`mcp_server.py`). Implement the primary orchestrator that sequentially kicks off extraction, clustering, reporting, and emailing via exposed REST endpoints (`/mcp/run-weekly-pulse`).

**Evaluation Criteria:**
- The FastAPI application launches successfully on `localhost:8000`.
- Health endpoint (`/health`) returns an `OK` API status.
- Tool endpoints (e.g., `/mcp/tools/fetch-reviews`) handle JSON payloads appropriately.

**Edge Cases:**
- Port conflicts if `8000` is already in use by another Kuvera local service.
- Timeouts when the `/mcp/run-weekly-pulse` endpoint takes up to 20 mins to process everything synchronously (may require background task decoupling).

---

### Phase 7: Testing & Validation
**Description:** 
Establish the automated testing suite (`tests/test_integration.py`). Ensure every phase of the pipeline natively supports "mock data" to prevent consuming free-tier API tokens or abusing store APIs unnecessarily during development. 

**Evaluation Criteria:**
- Running `pytest tests/ -v` passes unequivocally on all core logic endpoints.
- Cost constraints (validated via `cost_calculator.py`) match estimates.

**Edge Cases:**
- Tests randomly failing due to mock asynchronous timing issues.
- Missing mock fixtures for newly added custom Kuvera taxonomy categories.

---

### Phase 8: Deployment & Scheduling
**Description:** 
Finalize the orchestration script (`scripts/run_weekly_pulse.py` and `scripts/scheduler.py`). Containerize the application (Docker) and deploy to a production instance configured to fire every Monday at 9:00 AM. 

**Evaluation Criteria:**
- Scheduled CRON or `schedule` framework activates automatically at 09:00 AM on Monday.
- Logs correctly append to `data/logs/*.log` showing complete life cycle and execution speed.
- Weekly runs execute effectively without manual intervention.

**Edge Cases:**
- System clock drifts or timezone misconfigurations launching reports on the wrong day.
- Server restart unregistering the local cron scheduler.
- Container running out of disk space from persisted PDFs over time if a retention policy isn't configured.

---

## 📝 Success Criteria Recap for Kuvera
- **Cost:** **$0.00** flat operations cost (utilizing local inference or free-tier Open Source APIs via Groq/Together).
- **Time to insight:** ~20 minutes maximum total execution per week.
- **Reporting Quality:** Minimum 5-7 confident themes identified out of up to 1000 reviews.
- **Adoption:** Regular opening and actionable insights generated for Product, Support, and Leadership teams.
