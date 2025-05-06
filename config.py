# config.py – כולל משקלי מקורות וסף דעיכה

WHITELISTED_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "TSLA"]
TRADE_THRESHOLD = 0.4  # רמת בטחון מינימלית להמלצה
SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META"]

# משקלי מקורות לניתוח סנטימנט
SOURCE_WEIGHTS = {
    'Bloomberg': 1.3,
    'CNBC': 1.2,
    'Yahoo Finance': 1.0,
    'Unknown': 0.8
}

# קבוע דעיכה אקספוננציאלי לפי זמן (בשעות)
LAMBDA_DECAY = 0.1
