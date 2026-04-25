# Google OAuth 2.0 Setup Guide

This guide walks you through setting up and using the Gmail OAuth 2.0 authentication flow for Kuvera Weekly Pulse.

## Overview

The system now supports **two methods** for sending emails:
1. **OAuth 2.0 (Recommended)** - Secure, no password needed, uses Gmail API
2. **SMTP (Fallback)** - Traditional email/password method

OAuth is now the **primary method**. The system will automatically try OAuth first and fall back to SMTP if OAuth credentials aren't available.

---

## Method 1: OAuth 2.0 Setup (Recommended)

### Step 1: Google Cloud Console Configuration

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create a new project or select an existing one

2. **Enable Gmail API**
   - Navigate to: APIs & Services > Library
   - Search for "Gmail API"
   - Click "Enable"

3. **Configure OAuth Consent Screen**
   - Go to: APIs & Services > OAuth consent screen
   - Choose "External" user type (unless you have a Google Workspace account)
   - Fill in required fields:
     - App name: `Kuvera Weekly Pulse`
     - User support email: Your email
     - Developer contact email: Your email
   - Add scopes:
     - `.../auth/gmail.send` - Send emails on your behalf
     - `.../auth/gmail.readonly` - Read your Gmail profile
     - `.../auth/userinfo.profile` - View your basic profile info
     - `.../auth/userinfo.email` - View your email address

4. **Create OAuth 2.0 Credentials**
   - Go to: APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: **Web application**
   - Name: `Kuvera Pulse Backend`
   - Authorized redirect URIs:
     - For local development: `http://localhost:8000/oauth/callback`
     - For production (Render): `https://your-app-name.onrender.com/oauth/callback`
   - Click "Create"
   - **Copy the Client ID and Client Secret**

### Step 2: Configure Your Application

#### Option A: Update Environment Variables (Recommended)

Add these to your `.env` file or Render environment variables:

```env
GOOGLE_CLIENT_ID=your-client-id-from-google-cloud-console
GOOGLE_CLIENT_SECRET=your-client-secret-from-google-cloud-console
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
```

For production (Render):
```env
GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/oauth/callback
```

#### Option B: Use Your Own Credentials

**Important**: Get your OAuth credentials from Google Cloud Console:
1. Go to: https://console.cloud.google.com/
2. Navigate to: APIs & Services > Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Copy the Client ID and Client Secret
5. Add them to your `.env` file

**Never commit your credentials to version control!**

### Step 3: Complete OAuth Authorization

#### Local Development:

1. **Start the backend server**
   ```bash
   cd backend
   python mcp_server.py
   ```

2. **Initiate OAuth Flow**
   
   Open your browser and visit:
   ```
   http://localhost:8000/oauth/authorize
   ```
   
   OR use the API directly:
   ```bash
   curl http://localhost:8000/oauth/authorize
   ```

3. **Grant Permission**
   - You'll be redirected to Google's consent screen
   - Sign in with your Google account
   - Click "Allow" to grant permissions
   - You'll be redirected back to: `http://localhost:8000/oauth/callback`

4. **Verify Authorization**
   
   Check OAuth status:
   ```bash
   curl http://localhost:8000/oauth/status
   ```
   
   Expected response:
   ```json
   {
     "authenticated": true,
     "user": {
       "email": "your-email@gmail.com",
       "messages_total": 12345
     },
     "token_expiry": "2026-04-27T10:30:00",
     "message": "OAuth credentials are valid and ready to use"
   }
   ```

5. **Send Test Email**
   ```bash
   curl -X POST http://localhost:8000/oauth/test-email
   ```
   
   This will send a test email to your own Gmail account to verify the integration.

#### Production (Render):

1. **Update Redirect URI**
   - In Google Cloud Console, add your Render URL:
     `https://your-app-name.onrender.com/oauth/callback`
   
2. **Update Environment Variable**
   ```env
   GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/oauth/callback
   ```

3. **Complete Authorization**
   - Visit: `https://your-app-name.onrender.com/oauth/authorize`
   - Follow the same steps as local development

### Step 4: Use OAuth to Send Emails

Once authorized, emails will automatically use OAuth. You can:

#### Via API:
```bash
curl -X POST http://localhost:8000/mcp/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Product Team",
    "recipient_email": "stakeholder@example.com"
  }'
```

#### Via Frontend Dashboard:
1. Run the weekly pulse to generate reports
2. Click "Send Mail" button on any stakeholder draft
3. Enter recipient email
4. Email will be sent with PDF attachment via Gmail API

---

## Method 2: SMTP (Fallback)

If OAuth is not configured, the system falls back to SMTP authentication.

### Setup:

Add to `.env`:
```env
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Important**: 
- Enable 2-Factor Authentication on your Google account
- Generate an App Password at: https://myaccount.google.com/apppasswords
- Use the App Password, NOT your regular Gmail password

---

## OAuth Management Endpoints

### Check Authentication Status
```bash
GET /oauth/status
```

### Revoke Credentials (Logout)
```bash
POST /oauth/logout
```

This will:
- Revoke the access token with Google
- Delete the local `token.json` file
- Require re-authorization on next use

### Re-authorize
After logout or token expiry, simply visit `/oauth/authorize` again.

---

## How It Works

### OAuth Flow Diagram

```
User Browser                    Backend Server                    Google OAuth
     |                              |                                  |
     |-- GET /oauth/authorize ----->|                                  |
     |                              |-- Authorization URL ------------>|
     |<- Redirect to Google --------|                                  |
     |                              |                                  |
     |-------- User Grants Permission -------------------------------->|
     |                              |                                  |
     |<- Callback with code --------|                                  |
     |   GET /oauth/callback        |                                  |
     |                              |                                  |
     |                              |-- Exchange code for tokens ------>|
     |                              |<- Access + Refresh tokens -------|
     |                              |                                  |
     |                              |-- Save token.json ---------------|
     |<- Success response ----------|                                  |
     |                              |                                  |
     |                              |                                  |
     |-- POST /mcp/send-email ----->|                                  |
     |                              |-- Use access token ------------->|
     |                              |<- Email sent -------------------|
     |<- Success --------------------|                                  |
```

### Token Management

- **Access Token**: Valid for ~1 hour, used for API calls
- **Refresh Token**: Long-lived, used to get new access tokens
- **Auto-refresh**: System automatically refreshes expired tokens
- **Storage**: Tokens stored in `backend/data/tokens/token.json`

### Security Features

✅ **State Parameter**: Prevents CSRF attacks  
✅ **Offline Access**: Refresh tokens for long-term access  
✅ **Token Auto-refresh**: Seamless user experience  
✅ **Secure Storage**: Local token file with proper permissions  
✅ **Revocable**: Users can revoke access anytime  

---

## Troubleshooting

### Issue: "No valid OAuth credentials"

**Solution**: Complete the OAuth authorization flow by visiting `/oauth/authorize`

### Issue: "Invalid redirect_uri"

**Solution**: Ensure the redirect URI in Google Cloud Console matches exactly:
- Local: `http://localhost:8000/oauth/callback`
- Production: `https://your-app.onrender.com/oauth/callback`

### Issue: "Token expired"

**Solution**: Tokens auto-refresh. If refresh fails, re-authorize via `/oauth/authorize`

### Issue: "Insufficient permissions"

**Solution**: Ensure all required scopes are added in Google Cloud Console:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/userinfo.profile`
- `https://www.googleapis.com/auth/userinfo.email`

### Issue: "App not verified"

**Solution**: For personal/testing use, click "Continue" on the warning screen. For production, submit your app for Google verification.

---

## Files Modified/Created

### New Files:
- `backend/tools/gmail_oauth.py` - OAuth implementation
- `backend/data/tokens/token.json` - Auto-created after authorization

### Modified Files:
- `backend/mcp_server.py` - Added OAuth endpoints and updated send-email
- `backend/.env` - Add OAuth environment variables (optional)

---

## Next Steps

1. ✅ Complete OAuth authorization
2. ✅ Send test email via `/oauth/test-email`
3. ✅ Run weekly pulse to generate reports
4. ✅ Send stakeholder emails with PDF attachments
5. ✅ Monitor OAuth status via `/oauth/status`

---

## Production Checklist

- [ ] Add production redirect URI to Google Cloud Console
- [ ] Update `GOOGLE_REDIRECT_URI` environment variable
- [ ] Complete OAuth authorization on production
- [ ] Test email sending in production
- [ ] Move Client ID/Secret to environment variables (security best practice)
- [ ] Consider submitting app for Google verification (if needed)
- [ ] Set up monitoring for token expiry
- [ ] Document OAuth process for team members

---

**Need Help?** Check the logs in `backend/data/logs/mcp_server.log` for detailed error messages.
