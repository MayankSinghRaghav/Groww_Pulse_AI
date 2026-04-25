# 🚀 OAuth 2.0 Quick Start

Get Gmail OAuth 2.0 working in **5 minutes**!

---

## Prerequisites

✅ Python 3.8+ installed  
✅ Google account (Gmail)  
✅ Dependencies installed (`pip install -r requirements.txt`)

---

## Method 1: Automated Setup (Easiest)

### Windows

```bash
# Run the setup script
setup_oauth.bat

# In a NEW terminal, run the test
cd backend
python test_oauth.py
```

### Mac/Linux

```bash
# Start the server
cd backend
python mcp_server.py

# In a NEW terminal, run the test
python test_oauth.py
```

---

## Method 2: Manual Setup

### Step 1: Start the Backend Server

```bash
cd backend
python mcp_server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Complete OAuth Authorization

Open your browser and visit:
```
http://localhost:8000/oauth/authorize
```

**What happens:**
1. You'll be redirected to Google's consent screen
2. Sign in with your Google account
3. Review the permissions:
   - ✅ Send emails on your behalf
   - ✅ View your email address
   - ✅ View your basic profile info
4. Click **"Allow"**

### Step 3: Verify Authorization

You'll be redirected back to:
```
http://localhost:8000/oauth/callback
```

You should see a success message:
```json
{
  "status": "success",
  "message": "OAuth authorization completed successfully!",
  "user": {
    "email": "your-email@gmail.com",
    "messages_total": 12345
  }
}
```

### Step 4: Test Email Sending

```bash
curl -X POST http://localhost:8000/oauth/test-email
```

Or use the test script:
```bash
python test_oauth.py
```

Check your Gmail inbox - you should receive a test email! 🎉

---

## Verify Everything Works

### Check OAuth Status

```bash
curl http://localhost:8000/oauth/status
```

Expected response:
```json
{
  "authenticated": true,
  "user": {
    "email": "your-email@gmail.com"
  },
  "message": "OAuth credentials are valid and ready to use"
}
```

### Send a Stakeholder Email

```bash
curl -X POST http://localhost:8000/mcp/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Product Team",
    "recipient_email": "your-email@gmail.com"
  }'
```

---

## What Happened?

After successful authorization:

1. ✅ Google gave you an **access token** (valid for 1 hour)
2. ✅ Google gave you a **refresh token** (long-lived)
3. ✅ Tokens saved to `backend/data/tokens/token.json`
4. ✅ System will auto-refresh expired tokens
5. ✅ You can now send emails via Gmail API!

---

## Common Commands

```bash
# Check authentication status
curl http://localhost:8000/oauth/status

# Send test email
curl -X POST http://localhost:8000/oauth/test-email

# Revoke access (logout)
curl -X POST http://localhost:8000/oauth/logout

# Re-authorize (if needed)
# Just visit: http://localhost:8000/oauth/authorize
```

---

## Troubleshooting

### "No valid OAuth credentials"
**Solution**: Complete the authorization flow by visiting `/oauth/authorize`

### "Invalid redirect_uri"
**Solution**: This should work out of the box for local development. The redirect URI is configured as `http://localhost:8000/oauth/callback`

### "App not verified" warning
**Solution**: This is normal for testing. Click "Continue" to proceed.

### Server won't start
**Solution**: 
```bash
# Check if port 8000 is in use
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Kill the process or use a different port
```

---

## Next Steps

✅ OAuth is working  
✅ You can send emails  
✅ Now run the weekly pulse!

```bash
# Run the full pipeline
python scripts/run_weekly_pulse.py

# Or via API
curl -X POST http://localhost:8000/mcp/run-weekly-pulse \
  -H "Content-Type: application/json" \
  -d '{"app_name": "Kuvera", "weeks": 8}'
```

---

## Need More Help?

📖 **Full Setup Guide**: `docs/OAuth_Setup_Guide.md`  
📊 **Visual Flow Diagram**: `docs/OAuth_Flow_Diagram.md`  
📝 **Implementation Details**: `OAUTH_IMPLEMENTATION.md`  
🔧 **Test Commands**: `oauth_commands.sh`  

---

## Security Note

⚠️ **For Production**: Move OAuth credentials to environment variables:

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-app.onrender.com/oauth/callback
```

The credentials are currently hardcoded for easy setup, but should be moved to `.env` for production use.

---

**That's it! You're ready to send emails securely with OAuth 2.0!** 🎊
