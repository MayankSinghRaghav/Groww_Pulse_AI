# OAuth 2.0 Flow - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KUVERA WEEKLY PULSE                          │
│                                                                     │
│  ┌──────────────────┐              ┌──────────────────────────┐    │
│  │   Frontend       │              │   Backend (FastAPI)      │    │
│  │   (Vercel)       │              │   (Render)               │    │
│  │                  │              │                          │    │
│  │  • Dashboard     │◄────────────►│  • MCP Server            │    │
│  │  • Send Emails   │  HTTP/API    │  • OAuth Endpoints       │    │
│  │  • View Reports  │              │  • Gmail OAuth Module    │    │
│  └──────────────────┘              │  • Email Draft Tools     │    │
│                                    │  • Report Generation     │    │
│                                    └──────────────────────────┘    │
│                                             │                       │
└─────────────────────────────────────────────┼───────────────────────┘
                                              │
                                   OAuth 2.0 / Gmail API
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Google Cloud    │
                                    │                  │
                                    │  • OAuth Server  │
                                    │  • Gmail API     │
                                    │  • User Consent  │
                                    └──────────────────┘
```

---

## OAuth 2.0 Authorization Flow

### Step-by-Step Visualization

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│   User       │                    │   Kuvera     │                    │   Google     │
│   Browser    │                    │   Backend    │                    │   OAuth      │
│              │                    │   Server     │                    │   Server     │
└──────┬───────┘                    └──────┬───────┘                    └──────┬───────┘
       │                                   │                                   │
       │                                   │                                   │
       │  1. Click "Authorize"             │                                   │
       │──────────────────────────────────>│                                   │
       │                                   │                                   │
       │                                   │  2. Generate Auth URL             │
       │                                   │     + State Parameter             │
       │                                   │──────────────────────────────────>│
       │                                   │                                   │
       │  3. HTTP 302 Redirect             │                                   │
       │     (to Google Consent Screen)    │                                   │
       │<─────────────────────────────────────────────────────────────────────│
       │                                   │                                   │
       │                                   │                                   │
       │  4. User sees consent screen      │                                   │
       │     "Kuvera Pulse wants to:"      │                                   │
       │     • Send emails                 │                                   │
       │     • View profile                │                                   │
       │                                   │                                   │
       │  5. User clicks "Allow"           │                                   │
       │─────────────────────────────────────────────────────────────────────>│
       │                                   │                                   │
       │                                   │                                   │
       │  6. HTTP 302 Redirect             │                                   │
       │     (back to callback URL)        │                                   │
       │     ?code=AUTH_CODE               │                                   │
       │     &state=STATE_TOKEN            │                                   │
       │──────────────────────────────────>│                                   │
       │                                   │                                   │
       │                                   │  7. Verify State Parameter        │
       │                                   │     (CSRF Protection)             │
       │                                   │                                   │
       │                                   │  8. Exchange Auth Code            │
       │                                   │     for Access + Refresh Tokens   │
       │                                   │──────────────────────────────────>│
       │                                   │                                   │
       │                                   │  9. Return Tokens                 │
       │                                   │<──────────────────────────────────│
       │                                   │                                   │
       │                                   │  10. Save tokens to               │
       │                                   │      data/tokens/token.json       │
       │                                   │                                   │
       │  11. Success Response             │                                   │
       │     {status: "success",           │                                   │
       │      user: {...}}                 │                                   │
       │<──────────────────────────────────│                                   │
       │                                   │                                   │
       ▼                                   ▼                                   ▼
```

---

## Token Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     TOKEN LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────┘

  Authorization
       │
       ▼
┌──────────────┐
│ Auth Code    │  Short-lived (single use)
│ (10 min)     │  Used to get tokens
└──────┬───────┘
       │
       │ Exchange
       ▼
┌──────────────────────────────────────────┐
│           Token Pair                      │
│                                          │
│  ┌────────────────┐  ┌────────────────┐ │
│  │ Access Token   │  │ Refresh Token  │ │
│  │                │  │                │ │
│  │ • 1 hour TTL   │  │ • Long-lived   │ │
│  │ • API calls    │  │ • Get new      │ │
│  │ • Expires      │  │   access token │ │
│  └───────┬────────┘  └───────┬────────┘ │
│          │                   │          │
└──────────┼───────────────────┼──────────┘
           │                   │
           │ Expired           │ Valid
           ▼                   ▼
┌──────────────────┐   ┌──────────────────┐
│ Need New Token   │   │ Use Refresh Token│
│                  │   │ to get new       │
│ Check if Refresh │<──│ Access Token     │
│ Token valid?     │   │                  │
└──────┬───────────┘   └──────────────────┘
       │
       │ Valid          │ Expired
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Auto-Refresh │  │ Re-authorize │
│              │  │ User must    │
│ Get new      │  │ complete     │
│ Access Token │  │ OAuth flow   │
└──────────────┘  └──────────────┘
```

---

## Email Sending Flow (with OAuth)

```
┌─────────────────────────────────────────────────────────────────┐
│                  EMAIL SENDING FLOW                              │
└─────────────────────────────────────────────────────────────────┘

User Action: Send Stakeholder Email
       │
       ▼
┌──────────────────────────┐
│ POST /mcp/send-email     │
│ {                        │
│   role: "Product Team",  │
│   recipient: "..."       │
│ }                        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Check OAuth Credentials  │
│                          │
│ Load token.json          │
│ Check expiry             │
└────────────┬─────────────┘
             │
      ┌──────┴──────┐
      │             │
   Valid         Expired/Missing
      │             │
      ▼             ▼
┌──────────┐  ┌──────────────────┐
│ Use      │  │ Try Refresh      │
│ OAuth    │  │                  │
│ (Gmail   │  └──────┬───────────┘
│  API)    │         │
│          │    ┌────┴────┐
│          │    │         │
│          │  Success   Failed
│          │    │         │
│          │    ▼         ▼
│          │  ┌──────┐ ┌────────────┐
│          │  │ Use  │ │ Fallback   │
│          │  │OAuth │ │ to SMTP    │
│          │  └──┬───┘ └─────┬──────┘
│          │     │           │
└──────────┼─────┘           │
           │                 │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ Send Email      │
           │                 │
           │ • Attach PDF    │
           │ • Send to       │
           │   recipient     │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ Success Response│
           │                 │
           │ {               │
           │   status: ok,   │
           │   method:       │
           │     "oauth" or  │
           │     "smtp",     │
           │   message_id:   │
           │     "..."       │
           │ }               │
           └─────────────────┘
```

---

## Fallback Logic

```
┌──────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FALLBACK                    │
└──────────────────────────────────────────────────────────────┘

                    Start: Send Email
                           │
                           ▼
                  ┌─────────────────┐
                  │ OAuth Configured│
                  │ ?               │
                  └────────┬────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                   YES           NO
                    │             │
                    ▼             │
           ┌──────────────┐      │
           │ Tokens Valid │      │
           │ ?            │      │
           └──────┬───────┘      │
                  │              │
           ┌──────┴──────┐      │
           │             │      │
          YES           NO      │
           │             │      │
           │             ▼      │
           │    ┌─────────────┐ │
           │    │ Refresh     │ │
           │    │ Possible?   │ │
           │    └──────┬──────┘ │
           │           │        │
           │    ┌──────┴──────┐ │
           │    │             │ │
           │   YES           NO │
           │    │             │ │
           ▼    ▼             ▼ ▼
┌──────────────────┐   ┌──────────────────┐
│ SEND VIA OAUTH   │   │ SMTP Configured  │
│                  │   │ ?                │
│ Gmail API        │   └────────┬─────────┘
│ Secure           │            │
│ No password      │     ┌──────┴──────┐
│ Modern           │     │             │
└──────────────────┘    YES           NO
                         │             │
                         ▼             ▼
                ┌──────────────┐ ┌──────────────┐
                │ SEND VIA SMTP│ │ ERROR        │
                │              │ │              │
                │ Legacy       │ │ Neither OAuth│
                │ Requires pwd │ │ nor SMTP     │
                │ Fallback     │ │ configured   │
                └──────────────┘ └──────────────┘
```

---

## Data Flow - Token Storage

```
┌──────────────────────────────────────────────────────────────┐
│                    TOKEN STORAGE                              │
└──────────────────────────────────────────────────────────────┘

After OAuth Authorization:

  backend/
  └── data/
      └── tokens/
          └── token.json  ← Created automatically
              │
              ├─ token: "ya29.a0AX..."        (Access Token)
              ├─ refresh_token: "1//0abc..."   (Refresh Token)
              ├─ token_uri: "https://..."      (Token Endpoint)
              ├─ client_id: "79847022310..."   (Your Client ID)
              ├─ client_secret: "GOCSPX-..."   (Your Client Secret)
              ├─ scopes: [...]                  (Permissions)
              └─ expiry: "2026-04-27T..."      (Expiry Time)


On Each API Call:

  1. Load token.json
  2. Check expiry
  3. If expired and refresh_token exists:
     ├─ Request new access token from Google
     ├─ Update token.json with new token
     └─ Use new token for API call
  4. If valid:
     └─ Use token directly
```

---

## Security Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SECURITY MEASURES                          │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 1. State Parameter (CSRF Protection)                        │
│                                                             │
│    Generate random state ──► Store in oauth_state.json     │
│         │                                                    │
│         ▼                                                    │
│    Include in auth URL ──► Google returns it in callback    │
│         │                                                    │
│         ▼                                                    │
│    Compare with stored ──► Match? Continue : Reject         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. Scoped Permissions                                       │
│                                                             │
│    Only request what's needed:                              │
│    ✓ gmail.send        (Send emails)                        │
│    ✓ gmail.readonly    (Read profile)                       │
│    ✓ userinfo.profile  (Basic profile)                      │
│    ✓ userinfo.email    (Email address)                      │
│                                                             │
│    ✗ NO full account access                                 │
│    ✗ NO unnecessary permissions                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. Token Refresh (Auto)                                     │
│                                                             │
│    Access Token Expires (1 hour)                            │
│         │                                                    │
│         ▼                                                    │
│    Use Refresh Token ──► Get new Access Token               │
│         │                                                    │
│         ▼                                                    │
│    Update token.json ──► Seamless user experience           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 4. Revocable Access                                         │
│                                                             │
│    User can revoke anytime:                                 │
│    • Via /oauth/logout endpoint                             │
│    • Via Google Account settings                            │
│    • Deletes local token.json                               │
│    • Revokes token with Google                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Production Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    PRODUCTION SETUP                           │
└──────────────────────────────────────────────────────────────┘

  Google Cloud Console
  ┌─────────────────────────┐
  │ OAuth 2.0 Client ID     │
  │                         │
  │ Authorized Redirect URIs│
  │ • https://app.render.com│  ← Production URL
  │   /oauth/callback       │
  └─────────────────────────┘
             │
             │ OAuth Flow
             ▼
  ┌─────────────────────────┐
  │   Render (Backend)      │
  │                         │
  │ Environment Variables:  │
  │ • GOOGLE_CLIENT_ID      │
  │ • GOOGLE_CLIENT_SECRET  │
  │ • GOOGLE_REDIRECT_URI   │
  │                         │
  │ Token Storage:          │
  │ • Ephemeral (lost on    │
  │   restart)              │
  │ • Consider: Redis/DB    │
  └─────────────────────────┘
             │
             │ API Calls
             ▼
  ┌─────────────────────────┐
  │   Vercel (Frontend)     │
  │                         │
  │ • Static HTML           │
  │ • Calls backend API     │
  │ • Displays results      │
  └─────────────────────────┘
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│                    OAUTH ENDPOINTS                            │
└──────────────────────────────────────────────────────────────┘

  GET  /oauth/authorize      Start OAuth flow
  GET  /oauth/callback       Handle callback (auto)
  GET  /oauth/status         Check auth status
  POST /oauth/logout         Revoke credentials
  POST /oauth/test-email     Send test email

┌──────────────────────────────────────────────────────────────┐
│                    KEY FILES                                  │
└──────────────────────────────────────────────────────────────┘

  tools/gmail_oauth.py       OAuth implementation
  data/tokens/token.json     Stored tokens (auto-created)
  docs/OAuth_Setup_Guide.md  Setup documentation
  test_oauth.py              Test script

┌──────────────────────────────────────────────────────────────┐
│                    COMMON COMMANDS                            │
└──────────────────────────────────────────────────────────────┘

  # Start server
  python mcp_server.py

  # Check status
  curl http://localhost:8000/oauth/status

  # Authorize
  Open: http://localhost:8000/oauth/authorize

  # Test email
  curl -X POST http://localhost:8000/oauth/test-email

  # Logout
  curl -X POST http://localhost:8000/oauth/logout
```

---

This visual guide provides a complete understanding of how OAuth 2.0 is implemented in the Kuvera Weekly Pulse system. For detailed setup instructions, see `docs/OAuth_Setup_Guide.md`.
