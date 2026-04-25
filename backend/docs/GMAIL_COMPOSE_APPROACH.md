# Gmail Compose URL Approach

## Overview

The system now uses **Gmail Compose URLs** to open Gmail's compose window with pre-filled content. This approach:

✅ Opens Gmail compose in a new tab  
✅ Pre-fills subject line  
✅ Pre-fills email body  
✅ Provides PDF download link  
✅ **User manually attaches PDF and sends**  

---

## How It Works

### User Flow

1. **Click "Compose in Gmail"** button on dashboard
2. **Enter recipient email** (optional prompt)
3. **Gmail compose opens** in new tab with:
   - Subject pre-filled
   - Body pre-filled with PDF download link
4. **Download PDF** from the link in email body
5. **Attach PDF** to email manually (drag & drop)
6. **Enter recipient** if not pre-filled
7. **Click Send** in Gmail

---

## API Endpoint

### GET /mcp/gmail-compose

Generates a Gmail compose URL with pre-filled content.

**Parameters:**
- `role` (required): "Product Team", "Support Team", or "Leadership"
- `recipient_email` (optional): Pre-fill recipient address

**Example:**
```bash
curl "http://localhost:8000/mcp/gmail-compose?role=Product%20Team&recipient_email=test@example.com"
```

**Response:**
```json
{
  "status": "success",
  "role": "Product Team",
  "pdf_exists": true,
  "pdf_filename": "Kuvera_Pulse_Product_Team_20260426.pdf",
  "pdf_download_url": "http://localhost:8000/mcp/download-note/Kuvera_Pulse_Product_Team_20260426.pdf",
  "gmail_compose_url": "https://mail.google.com/mail/?view=cm&to=test%40example.com&subject=...&body=...",
  "recipient_email": "test@example.com",
  "subject": "[Kuvera Weekly Pulse] April 26, 2026 — Product Team Briefing",
  "instructions": {
    "step1": "Click the Gmail compose URL to open Gmail",
    "step2": "Download the PDF from the link provided in the email body",
    "step3": "Attach the PDF to the email manually",
    "step4": "Enter recipient email address if not pre-filled",
    "step5": "Review the email and click Send"
  }
}
```

---

## Gmail Compose URL Format

The URL format is:
```
https://mail.google.com/mail/?view=cm&to=RECIPIENT&subject=SUBJECT&body=BODY
```

**Parameters:**
- `view=cm` - Opens compose window
- `to` - Recipient email address
- `subject` - Email subject (URL encoded)
- `body` - Email body text (URL encoded)

**Important Limitation:**
⚠️ Gmail compose URLs **cannot attach files directly**. The PDF must be downloaded and attached manually.

---

## Frontend Integration

The dashboard uses the `openGmailCompose()` function:

```javascript
function openGmailCompose(role) {
    // Get recipient email from user
    const recipient = prompt('Enter recipient email address (optional):');
    
    // Fetch compose URL from backend
    fetch(`${BACKEND_URL}/mcp/gmail-compose?role=${role}&recipient_email=${recipient}`)
        .then(response => response.json())
        .then(data => {
            // Show instructions
            // Open Gmail compose URL in new window
            window.open(data.gmail_compose_url, '_blank');
        });
}
```

---

## Testing

### 1. Generate PDF First

```bash
# Run the weekly pulse to generate PDFs
curl -X POST http://localhost:8000/mcp/run-weekly-pulse \
  -H "Content-Type: application/json" \
  -d '{"app_name": "Kuvera", "weeks": 8}'
```

### 2. Test Compose URL Generation

```bash
# Test with Product Team role
curl "http://localhost:8000/mcp/gmail-compose?role=Product%20Team"

# Test with recipient email
curl "http://localhost:8000/mcp/gmail-compose?role=Leadership&recipient_email=ceo@kuvera.in"
```

### 3. Test in Browser

1. Open dashboard: `http://localhost:8000` (or your Vercel URL)
2. Click "Compose in Gmail" button
3. Gmail compose window opens in new tab
4. Download PDF from link in body
5. Attach PDF manually
6. Send email

---

## Comparison: Compose URL vs OAuth API

| Feature | Gmail Compose URL | Gmail OAuth API |
|---------|------------------|-----------------|
| **Setup** | ✅ No setup needed | ❌ Requires OAuth configuration |
| **Authentication** | ✅ User logged into Gmail | ❌ Requires OAuth flow |
| **PDF Attachment** | ⚠️ Manual (download + attach) | ✅ Automatic (via API) |
| **User Control** | ✅ User reviews before sending | ❌ Sent automatically |
| **Complexity** | ✅ Simple URL | ❌ Complex OAuth flow |
| **Browser Required** | ✅ Yes | ❌ No (server-side) |
| **Best For** | Manual review workflow | Automated sending |

---

## Why This Approach?

This approach was chosen because:

1. **User wants control** - Review email before sending
2. **No OAuth setup** - Works immediately without configuration
3. **Simple workflow** - Just click and Gmail opens
4. **Manual attachment** - User controls what gets attached
5. **No credentials** - No API keys or passwords needed

---

## Troubleshooting

### Issue: "PDF note not found"
**Solution**: Run the weekly pulse first to generate PDFs
```bash
curl -X POST http://localhost:8000/mcp/run-weekly-pulse \
  -H "Content-Type: application/json" \
  -d '{"app_name": "Kuvera", "weeks": 8}'
```

### Issue: Pop-up blocked
**Solution**: Allow pop-ups for your dashboard URL in browser settings

### Issue: Gmail doesn't open
**Solution**: Ensure you're logged into Gmail in your browser

### Issue: Subject/body not pre-filled
**Solution**: Check browser console for errors, verify backend is running

---

## Files Modified

### New Files
- `backend/tools/gmail_compose.py` - Gmail compose URL generator

### Modified Files
- `backend/mcp_server.py` - Added `/mcp/gmail-compose` endpoint
- `frontend/index.html` - Updated to use `openGmailCompose()` function

---

## Next Steps

1. ✅ Backend server running
2. ✅ Weekly pulse executed (PDFs generated)
3. ✅ Click "Compose in Gmail" on dashboard
4. ✅ Download PDF from email body link
5. ✅ Attach PDF manually
6. ✅ Send email

---

**Note**: If you want automatic PDF attachment (no manual steps), use the OAuth API approach instead. See `OAUTH_IMPLEMENTATION.md` for details.
