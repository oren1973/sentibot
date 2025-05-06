# config.py – הרצת Debug ממוקדת ל־10 מניות נבחרות

# סימבולים לבדיקה ממוקדת (Debug mode)
SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META", "PFE", "XOM", "JPM", "DIS", "WMT"]

# רמת בטחון מינימלית להמלצה
TRADE_THRESHOLD = 0.4

# משקלי מקורות לניתוח סנטימנט
SOURCE_WEIGHTS = {
    'Bloomberg': 1.3,
    'CNBC': 1.2,
    'Yahoo Finance': 1.0,
    'Unknown': 0.8
}

# קבוע דעיכה אקספוננציאלי לפי זמן (בשעות)
LAMBDA_DECAY = 0.1
