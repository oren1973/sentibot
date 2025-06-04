# cnbc_scraper.py
import feedparser
import socket
from settings import setup_logger, MIN_HEADLINE_LENGTH

logger = setup_logger(__name__)

KEYWORDS_BY_SYMBOL = {
    "TSLA": ["Tesla", "Elon Musk", "TSLA"],
    "NVDA": ["Nvidia", "Jensen Huang", "NVDA", "GPU"],
    "AAPL": ["Apple", "AAPL", "iPhone", "MacBook", "iPad", "Tim Cook"],
    "MSFT": ["Microsoft", "MSFT", "Azure", "Windows", "Satya Nadella", "OpenAI"],
    "META": ["Meta", "Facebook", "META", "Instagram", "WhatsApp", "Zuckerberg"],
    "AMZN": ["Amazon", "AMZN", "AWS", "Bezos", "Prime"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "GOOG", "Android", "Search", "Sundar Pichai", "Waymo"],
    "GOOG": ["Google", "Alphabet", "GOOG", "Android", "Search", "Sundar Pichai", "Waymo"],
    "PFE": ["Pfizer", "PFE", "BioNTech"],
    "XOM": ["Exxon", "ExxonMobil", "XOM", "oil", "gas"],
    "JPM": ["JPMorgan", "JPM", "Jamie Dimon", "Chase"],
    "DIS": ["Disney", "DIS", "Disney+", "ESPN", "parks"],
    "WMT": ["Walmart", "WMT", "retail"],
    "GME": ["GameStop", "GME", "Gamestop"],
    "AMC": ["AMC", "AMC Entertainment"],
    "PLTR": ["Palantir", "PLTR"],
    "COIN": ["Coinbase", "COIN", "crypto"],
    "MSTR": ["MicroStrategy", "MSTR", "Saylor", "Bitcoin"],
    "BYND": ["Beyond Meat", "BYND"],
    "RIVN": ["Rivian", "RIVN"],
    "AFRM": ["Affirm", "AFRM"],
    "SOFI": ["SoFi", "SOFI"],
    "BB": ["BlackBerry", "BB"],
    "BBBYQ": ["Bed Bath", "BBBYQ"],
    "NIO": ["NIO Inc", "NIO"],
    "LCID": ["Lucid", "Lucid Motors", "LCID"],
    "NKLA": ["Nikola", "NKLA"],
    "SNAP": ["Snap", "Snapchat", "SNAP"],
}

def get_cnbc_titles(symbol: str, cnbc_general_rss_url: str, max_feed_items_to_scan: int = 50) -> list[tuple[str, str]]:
    source_name = "CNBC"
    symbol_upper = symbol.upper()
    keywords_for_symbol = KEYWORDS_BY_SYMBOL.get(symbol_upper, [symbol_upper]) 
    headlines = []

    if not cnbc_general_rss_url:
        logger.error(f"CNBC general RSS URL not provided. Cannot fetch news for {symbol_upper}.")
        return []

    logger.info(f"Fetching news for '{symbol_upper}' from {source_name} using keywords: {keywords_for_symbol} (Scanning up to {max_feed_items_to_scan} feed items from {cnbc_general_rss_url})")

    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(15)
    try:
        feed = feedparser.parse(cnbc_general_rss_url)

        if feed.bozo:
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name}. Reason: {bozo_reason} (URL: {cnbc_general_rss_url})")
            return []
        
        if not feed.entries:
            logger.info(f"No entries found in general RSS feed from {source_name}. (URL: {cnbc_general_rss_url})")
            return []

        logger.debug(f"Scanning {len(feed.entries)} total entries from {source_name} for '{symbol_upper}' (limit scan to {max_feed_items_to_scan})...")
        
        relevant_headlines_count = 0
        for entry in feed.entries[:max_feed_items_to_scan]:  
            title = entry.get("title", "").strip()
            
            if not title or len(title) < MIN_HEADLINE_LENGTH: 
                continue

            if any(keyword.lower() in title.lower() for keyword in keywords_for_symbol):
                headlines.append((title, source_name))
                relevant_headlines_count += 1
                logger.debug(f"    Found relevant title for '{symbol_upper}': '{title}'")
        
        logger.info(f"Found {len(headlines)} relevant headlines for '{symbol_upper}' from {source_name} (scanned up to {max_feed_items_to_scan} feed items).")

    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for '{symbol_upper}': {e} (URL: {cnbc_general_rss_url})", exc_info=True)
    finally:
        socket.setdefaulttimeout(original_timeout)

    return headlines
