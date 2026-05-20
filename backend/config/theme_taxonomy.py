# Predefined theme taxonomy for Groww Pulsator
THEME_TAXONOMY = {
    "Onboarding": [
        "signup", "login", "register", "start", "tutorial", "guide", "onboarding", "otp", "welcome"
    ],
    "KYC": [
        "kyc", "documents", "verify", "verification", "aadhaar", "pan", "rejection", "approval", "failed"
    ],
    "Payments": [
        "payment", "fund purchase", "sip", "bank", "mandate", "success", "failure", "transaction", "amount", "debit"
    ],
    "Statements": [
        "statement", "cas", "report", "tax", "portfolio", "download", "summary", "gain", "loss", "history"
    ],
    "Withdrawals": [
        "withdrawal", "redeem", "payout", "sell", "transfer", "bank account", "processing time", "delay", "credit"
    ],
    "Performance & Stability": [
        "crash", "freeze", "slow", "lag", "bug", "error", "crashing", "performance", "stable", "stability"
    ],
    "Customer Support": [
        "support", "customer care", "help", "agent", "chat", "email", "reply", "response", "ticket"
    ]
}

def get_themes():
    return list(THEME_TAXONOMY.keys())

def get_keywords_for_theme(theme):
    return THEME_TAXONOMY.get(theme, [])
