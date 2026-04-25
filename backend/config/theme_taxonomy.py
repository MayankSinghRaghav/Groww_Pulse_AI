# Predefined theme taxonomy for Kuvera
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
        "withdrawal", "redeem", "payout", "sell", "transfer", "bank account", "time", "delay", "credit"
    ]
}

def get_themes():
    return list(THEME_TAXONOMY.keys())

def get_keywords_for_theme(theme):
    return THEME_TAXONOMY.get(theme, [])
