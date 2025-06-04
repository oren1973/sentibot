# settings.py – הגדרות מרכזיות לפרויקט Sentibot

import logging
import sys
import os

# --- הגדרות Logger ---
def setup_logger(name='sentibot', level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- הגדרות מקורות חדשות (NEWS_SOURCES_CONFIG) ---
# זהו המילון הראשי ש- news_aggregator.py (לאיסוף חדשות)
# ו- sentiment_analyzer.py (לקבלת משקלים) ישתמשו בו.
NEWS_SOURCES_CONFIG = {
    "Yahoo Finance": {
        "enabled": True, # האם לנסות לשלוף מהמקור הזה דרך news_aggregator
        "scraper_function_name": "get_yahoo_news", 
        "rss_url_template": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US",
        "weight": 1.0 # משקל לשימוש ב-sentiment_analyzer
    },
    "CNBC": {
        "enabled": True,
        "scraper_function_name": "get_cnbc_titles",
        "rss_url_template": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "weight": 1.2
    },
    "Investors.com": {
        "enabled": False, # נשאר מנוטרל זמנית בגלל בעיות parsing בפיד שלהם
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": False, # נשאר מנוטרל זמנית בגלל חסימות (401 Forbidden)
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}",
        "weight": 1.0
    },
    # --- הוספת הגדרות משקל למקורות Reddit ---
    # ה-scraper של Reddit נקרא בנפרד ב-main.py, לכן השדות 'enabled' ו-'scraper_function_name'
    # כאן הם רק placeholders כדי ש-sentiment_analyzer יוכל למצוא את המשקלים.
    "Reddit_Post": {
        "enabled": False, # לא רלוונטי לאיסוף דרך news_aggregator
        "scraper_function_name": None, # כנ"ל
        "weight": 1.0  # התאם את המשקל הזה לפי איך שאתה רואה את החשיבות של פוסטים מ-Reddit
    },
    "Reddit_Comment": {
        "enabled": False, # לא רלוונטי לאיסוף דרך news_aggregator
        "scraper_function_name": None, # כנ"ל
        "weight": 0.8  # לדוגמה: לתת פחות משקל לתגובות מאשר לפוסטים או למקורות חדשותיים
    }
}

# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10 # מגבלה על כמה כותרות מקסימום לקחת מכל מקור *בתוך* ה-news_aggregator
MIN_HEADLINE_LENGTH = 10 # אורך כותרת/טקסט מינימלי כדי שייחשב תקף
MAIN_MAX_TOTAL_HEADLINES = 50 # מגבלה כוללת של פריטים (כותרות+פוסטים) לעיבוד ב-main.py פר סמל

# --- ספי החלטה (עבור recommender.py) ---
# אלו ספים *זמניים* שהתאמנו בהרצה הקודמת. הם מניחים שהקלט ל-recommender
# הוא ממוצע של ציוני סנטימנט משוקללים, שהטווח שלהם יכול להיות למשל בין 0 ל-1.5.
# נצטרך לכייל אותם בצורה מבוססת נתונים בהמשך.
RECOMMENDER_THRESHOLD_BUY = 0.70
RECOMMENDER_THRESHOLD_SELL = 0.40 # ציון נמוך מזה יוביל ל-SELL (כרגע רק סגירת פוזיציית BUY)

# --- הגדרות Reddit (לקריאה על ידי reddit_scraper.py ו-main.py) ---
REDDIT_ENABLED = os.getenv("REDDIT_ENABLED", "True").lower() in ('true', '1', 't') # האם להפעיל את ה-scraper של Reddit
REDDIT_SUBREDDITS_STR = os.getenv("REDDIT_SUBREDDITS_LIST", "stocks,wallstreetbets,StockMarket,investing,options") # הוספתי options
REDDIT_SUBREDDITS = [sub.strip() for sub in REDDIT_SUBREDDITS_STR.split(',')]
try:
    REDDIT_LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "10"))
    REDDIT_COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "2"))
except ValueError:
    logger = setup_logger("settings_fallback") # לוגר למקרה שיש שגיאה לפני שהלוגר הראשי מאותחל
    logger.warning("Could not parse Reddit limit/comments parameters from environment variables. Using defaults.")
    REDDIT_LIMIT_PER_SUBREDDIT = 10
    REDDIT_COMMENTS_PER_POST = 2

# --- הגדרות Alpaca ---
# ודא שמשתני הסביבה ALPACA_API_KEY ו-ALPACA_SECRET_KEY מוגדרים
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" 
TRADE_QUANTITY = 1 

# --- נתיבים לקבצי לוג ודוחות ---
REPORTS_OUTPUT_DIR = "sentibot_reports" # שם התיקייה שבה יישמרו הדוחות
LEARNING_LOG_CSV_PATH = os.path.join(REPORTS_OUTPUT_DIR, "learning_log_cumulative.csv")

# --- רשימת סימולי המניות למעקב (מיובאת מ-smart_universe.py ב-main.py) ---
# המשתנה SYMBOLS עצמו מיובא מקובץ smart_universe.py בתוך main.py
