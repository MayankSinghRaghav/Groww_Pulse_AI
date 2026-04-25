# 🚀 Deployment Guide: Kuvera Weekly Pulse

This project is now structured for professional deployment.

## 📁 Folder Structure
- **`/backend`**: Python FastAPI server (MCP), Scrapers, and AI Engine. (Deploy on **Render/Railway**)
- **`/frontend`**: Static HTML Dashboard. (Deploy on **Vercel**)

---

## 🛠️ Phase 1: Backend (Render)
1.  Sign in to [Render.com](https://render.com/).
2.  Click **New +** > **Web Service**.
3.  Connect your repository and select the `backend` folder as the **Root Directory**.
4.  **Environment Variables:** Add your `GROQ_API_KEY`, `SMTP_EMAIL`, and `SMTP_PASSWORD` in the Render dashboard.
5.  **Build Command:** `pip install -r requirements.txt`
6.  **Start Command:** `uvicorn mcp_server:app --host 0.0.0.0 --port $PORT`

## 🛠️ Phase 2: Frontend (Vercel)
1.  Sign in to [Vercel.com](https://vercel.com/).
2.  Click **Add New** > **Project**.
3.  Select the `frontend` folder as the **Root Directory**.
4.  Vercel will automatically detect the `vercel.json` and deploy your interactive dashboard.

---

## ⚡ How it works in Production
1.  Your **Backend** runs the weekly pulse (can be scheduled via a CRON job or a simple tool like `cron-job.org` hitting the `/mcp/run-weekly-pulse` endpoint).
2.  The **Frontend** serves your latest dashboard. 
3.  Stakeholders can click **"Send to Gmail"** directly from the live Vercel URL!

---
*Developed for Kuvera by Antigravity AI.*
