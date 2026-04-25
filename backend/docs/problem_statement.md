# Problem Statement: Weekly Product Review Pulse AI Agent

## Overview
Build an AI Agent that automatically generates a weekly product review pulse using public App Store / Play Store reviews for a **Kuvera**.

## Objectives
The agent should:
1. **Ingest** reviews from the last 8–12 weeks.
2. **Analyze**: Use LLMs to detect themes and cluster reviews.
3. **Report**: Generate a concise, one-page weekly insight report.
4. **Draft**: Create an email summary for stakeholders.

## Key Requirement: MCP-based Agent
The system must be implemented as an AI agent using **Model Context Protocol (MCP)**:
- **Modular Tools**: Distinct tools for ingestion, clustering, summarization, and output generation.
- **Separation of Concerns**:
    - Data retrieval (reviews ingestion)
    - Reasoning (theme detection)
    - Output generation (report + email)
- **Re-runnable**: Pipeline must be repeatable for future weeks.

## Sample Output (Weekly Pulse)
### Kuvera — Weekly Review Pulse
**Period**: Last 8–12 weeks

#### Top Themes
1. **App Performance & Bugs**
   - Reports of lag, crashes during trading hours
   - Login/session timeout issues
2. **Customer Support Friction**
   - Slow response times
   - Unresolved ticket complaints
3. **UX & Feature Gaps**
   - Confusing navigation for portfolio insights
   - Missing advanced analytics

#### Real User Quotes
- “The app freezes exactly when the market opens, very frustrating.”
- “Support takes days to reply and doesn’t solve the issue.”
- “Good for beginners but lacks detailed analysis tools.”

#### Action Ideas
1. **Stabilize Peak-Time Performance**
   - Prioritize infra scaling during market hours
   - Add real-time crash monitoring dashboard
2. **Improve Support SLA Visibility**
   - Show expected response time inside app
   - Add ticket status tracking
3. **Enhance Power-User Features**
   - Introduce advanced portfolio analytics
   - Improve navigation for investments dashboard

## Value Proposition
- **Product Teams**: Prioritize roadmap based on real user pain points.
- **Support Teams**: Identify recurring complaints early.
- **Leadership**: Quick health snapshot of common sentiment.
