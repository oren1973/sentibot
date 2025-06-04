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
NEWS_SOURCES_CONFIG = {
    "Yahoo Finance": {
        "enabled": True,
        "scraper_function_name": "get_yahoo_news", 
        "rss_url_template": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US",
        "weight": 1.0
    },
    "CNBC": {
        "enabled": True,
        "scraper_function_name": "get_cnbc_titles",
        "rss_url_template": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "weight": 1.2
    },
    "Investors.com": {
        "enabled": False, # נשאר מנוטרל זמנית
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": False, # נשאר מנוטרל זמנית
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}",
        "weight": 1.0
    }
}

# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10
MIN_HEADLINE_LENGTH = 10
MAIN_MAX_TOTAL_HEADLINES = 50

# --- ספי החלטה (עבור recommender.py) ---
# התאם את הספים האלה לסקאלה של ציוני הסנטימנט המשוקללים!
RECOMMENDER_THRESHOLD_BUY = 0.75  # שונה שם והערך לדוגמה
RECOMMENDER_THRESHOLD_SELL = 0.35 # שונה שם והערך לדוגמה

# --- הגדרות Reddit ---
REDDIT_ENABLED = os.getenv("REDDIT_ENABLED", "True").lower() in ('true', '1', 't') # הפעלת Reddit כברירת מחדל
REDDIT_SUBREDDITS_STR = os.getenv("REDDIT_SUBREDDITS_LIST", "stocks,wallstreetbets,StockMarket,investing")
REDDIT_SUBREDDITS = [sub.strip() for sub in REDDIT_SUBREDDITS_STR.split(',')]
try:
    REDDIT_LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "10")) # הקטנתי קצת את ברירת המחדל
    REDDIT_COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "2"))   # הקטנתי קצת את ברירת המחדל
except ValueError:
    REDDIT_LIMIT_PER_SUBREDDIT = 10
    REDDIT_COMMENTS_PER_POST = 2

# --- הגדרות Alpaca ---
# ודא שמשתני הסביבה ALPACA_API_KEY ו-ALPACA_SECRET_KEY מוגדרים
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" # ל-Paper Trading
# ALPACA_BASE_URL = "https://api.alpaca.markets" # ל-Live Trading - היזהר!
TRADE_QUANTITY = 1 # כמות מניות לקנות/למכור בכל פקודה

# --- נתיבים לקבצי לוג ודוחות ---
REPORTS_OUTPUT_DIR = "sentibot_reports"
LEARNING_LOG_CSV_PATH = os.path.join(REPORTS_OUTPUT_DIR, "learning_log_cumulative.csv")
# קבצי דוחות יומיים ישמרו עם חותמת זמן בשם שלהם בתוך REPORTS_OUTPUT_DIR

# --- רשימת סימולי המניות למעקב (מיובאת מ-smart_universe.py ב-main) ---
# SYMBOLS מוגדר ב-smart_universe.py
