# yahoo_scraper.py
import feedparser
from logger_config import setup_logger

logger = setup_logger(__name__)

def get_yahoo_news(symbol: str) -> list[tuple[str, str]]:
    """
    מקבל סימבול ומחזיר רשימת tuples של (כותרת, מקור) מ-Yahoo Finance.
    מחזיר רשימה ריקה במקרה של שגיאה.
    """
    source_name = "Yahoo Finance"
    headlines = []
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US"

    logger.info(f"Fetching news for {symbol} from {source_name}...")

    try:
        feed = feedparser.parse(url, timeout=10)

        if feed.bozo:
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for {symbol}. Reason: {bozo_reason}")
            return []

        if not feed.entries:
            logger.info(f"No entries found in RSS feed from {source_name} for {symbol}.")
            return []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if title and len(title) >= 10: # בדיקת אורך מינימלי
                headlines.append((title, source_name))
            elif title:
                logger.debug(f"Skipping short title from {source_name} for {symbol}: '{title}'")
        
        logger.info(f"Found {len(headlines)} headlines for {symbol} from {source_name}.")

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from {source_name} for {symbol}: {e}", exc_info=True)
        
    return headlines
