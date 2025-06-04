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
        "enabled": False, 
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": False, 
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}",
        "weight": 1.0
    },
    # הוספת הגדרות משקל ל-Reddit
    "Reddit_Post": {
        "enabled": True, # 'enabled' כאן הוא רק placeholder, הפעלת Reddit נשלטת מ-REDDIT_ENABLED
        "scraper_function_name": None, # Reddit נאסף בנפרד, לא דרך news_aggregator הכללי
        "weight": 1.0  # התאם את המשקל הזה לפי הצורך
    },
    "Reddit_Comment": {
        "enabled": True, # כנ"ל
        "scraper_function_name": None, # כנ"ל
        "weight": 0.8  # לדוגמה, לתת פחות משקל לתגובות מאשר לפוסטים
    }
}

# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10
MIN_HEADLINE_LENGTH = 10
MAIN_MAX_TOTAL_HEADLINES = 50

# --- ספי החלטה (עבור recommender.py) ---
# נסה עם ערכים אלו, ונצטרך לכייל אותם בהמשך!
RECOMMENDER_THRESHOLD_BUY = 0.70  # אם ממוצע משוקלל (0..~1.5) גבוה מזה -> קניה
RECOMMENDER_THRESHOLD_SELL = 0.40 # אם ממוצע משוקלל נמוך מזה -> מכירה (כרגע רק לסגירת פוזיציה)

# --- הגדרות Reddit ---
REDDIT_ENABLED = os.getenv("REDDIT_ENABLED", "True").lower() in ('true', '1', 't')
REDDIT_SUBREDDITS_STR = os.getenv("REDDIT_SUBREDDITS_LIST", "stocks,wallstreetbets,StockMarket,investing")
REDDIT_SUBREDDITS = [sub.strip() for sub in REDDIT_SUBREDDITS_STR.split(',')]
try:
    REDDIT_LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "10"))
    REDDIT_COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "2"))
except ValueError:
    REDDIT_LIMIT_PER_SUBREDDIT = 10
    REDDIT_COMMENTS_PER_POST = 2

# --- הגדרות Alpaca ---
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" 
TRADE_QUANTITY = 1 

# --- נתיבים לקבצי לוג ודוחות ---
REPORTS_OUTPUT_DIR = "sentibot_reports"
LEARNING_LOG_CSV_PATH = os.path.join(REPORTS_OUTPUT_DIR, "learning_log_cumulative.csv")
