# OAuth 2.0 Testing Commands
# Use these curl commands to test the OAuth integration

# ==========================================
# 1. CHECK SERVER HEALTH
# ==========================================
curl http://localhost:8000/health

# ==========================================
# 2. CHECK OAUTH STATUS
# ==========================================
curl http://localhost:8000/oauth/status

# ==========================================
# 3. START OAUTH FLOW
# This will return a redirect URL or you can open in browser
# ==========================================
curl -v http://localhost:8000/oauth/authorize

# Or open in browser:
# http://localhost:8000/oauth/authorize

# ==========================================
# 4. AFTER AUTHORIZATION - CHECK STATUS
# ==========================================
curl http://localhost:8000/oauth/status | python -m json.tool

# ==========================================
# 5. SEND TEST EMAIL
# ==========================================
curl -X POST http://localhost:8000/oauth/test-email

# ==========================================
# 6. RUN WEEKLY PULSE
# ==========================================
curl -X POST http://localhost:8000/mcp/run-weekly-pulse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "Kuvera",
    "weeks": 8
  }'

# ==========================================
# 7. GET LATEST RESULTS
# ==========================================
curl http://localhost:8000/mcp/latest-results | python -m json.tool

# ==========================================
# 8. SEND STAKEHOLDER EMAIL
# ==========================================
curl -X POST http://localhost:8000/mcp/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Product Team",
    "recipient_email": "your-email@gmail.com"
  }'

# ==========================================
# 9. DOWNLOAD PDF NOTE
# ==========================================
# First, check what PDFs are available in data/outputs
# Then download:
curl http://localhost:8000/mcp/download-note/Kuvera_Pulse_Product_Team_20260426.pdf \
  --output test_download.pdf

# ==========================================
# 10. LOGOUT (REVOKE CREDENTIALS)
# ==========================================
curl -X POST http://localhost:8000/oauth/logout

# ==========================================
# EXAMPLE: COMPLETE WORKFLOW
# ==========================================
# 1. Start server: python mcp_server.py
# 2. Check status:
curl http://localhost:8000/oauth/status

# 3. If not authenticated, open browser:
#    http://localhost:8000/oauth/authorize

# 4. After authorization, verify:
curl http://localhost:8000/oauth/status | python -m json.tool

# 5. Send test email:
curl -X POST http://localhost:8000/oauth/test-email

# 6. Run the pulse:
curl -X POST http://localhost:8000/mcp/run-weekly-pulse \
  -H "Content-Type: application/json" \
  -d '{"app_name": "Kuvera", "weeks": 8}'

# 7. Send stakeholder email:
curl -X POST http://localhost:8000/mcp/send-email \
  -H "Content-Type: application/json" \
  -d '{"role": "Leadership", "recipient_email": "ceo@kuvera.in"}'
