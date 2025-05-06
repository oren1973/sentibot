# config.py – גרסה עם טעינה דינמית של כל מניות S&P 500 מקובץ CSV

import csv
import os

def load_sp500_symbols(csv_path="constituents.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"⚠️ הקובץ '{csv_path}' לא נמצא בספריה. ודא שהעלית אותו ל־GitHub!")
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row['Symbol'].strip() for row in reader if row['Symbol'].strip()]

SYMBOLS = load_sp500_symbols()

# רמת בטחון מינימלית להמלצה (לא בשימוש אם יש ספים מותאמים פר-מניה)
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
