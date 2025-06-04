# investors_scraper.py
import feedparser
import socket
from settings import setup_logger, MIN_HEADLINE_LENGTH

logger = setup_logger(__name__) 

def get_investors_news(symbol: str, rss_url_template: str) -> list[tuple[str, str]]:
    source_name = "Investors.com"
    headlines = []
    
    if not rss_url_template:
        logger.error(f"RSS URL template not provided for {source_name}. Cannot fetch news for {symbol}.")
        return []

    rss_url = rss_url_template.replace("{symbol}", symbol)
    logger.info(f"Fetching news for '{symbol}' from {source_name} using URL: {rss_url}")
    
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(15) # הגדלתי מעט את ה-timeout
    try:
        feed = feedparser.parse(rss_url) 

        if feed.bozo:
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for '{symbol}'. Reason: {bozo_reason} (URL: {rss_url})")
            return []

        if not feed.entries:
            logger.info(f"No entries found in RSS feed from {source_name} for '{symbol}'. (URL: {rss_url})")
            return []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if title and len(title) >= MIN_HEADLINE_LENGTH:
                headlines.append((title, source_name))
            elif title:
                logger.debug(f"Skipping short title from {source_name} for '{symbol}': '{title}' (Length: {len(title)})")
        
        logger.info(f"Found {len(headlines)} headlines for '{symbol}' from {source_name}.")

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from {source_name} for '{symbol}': {e} (URL: {rss_url})", exc_info=True)
    finally:
        socket.setdefaulttimeout(original_timeout)
    
    return headlines
