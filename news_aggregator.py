# news_aggregator.py

from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from marketwatch_scraper import fetch_marketwatch_titles
from cnbc_scraper import get_cnbc_titles

from settings import setup_logger, NEWS_SOURCES_CONFIG, DEFAULT_MAX_HEADLINES_PER_SOURCE, MIN_HEADLINE_LENGTH

logger = setup_logger(__name__)

AVAILABLE_SCRAPER_FUNCTIONS = {
    "get_yahoo_news": get_yahoo_news,
    "get_investors_news": get_investors_news,
    "fetch_marketwatch_titles": fetch_marketwatch_titles,
    "get_cnbc_titles": get_cnbc_titles,
}

def fetch_all_news(symbol: str, max_headlines_total: int = 50) -> list[tuple[str, str]]:
    all_collected_headlines = []
    seen_titles_lower = set() 

    logger.info(f"Starting news aggregation for symbol: '{symbol}'")

    for source_key, source_config in NEWS_SOURCES_CONFIG.items():
        if not source_config.get("enabled", False):
            logger.info(f"Source '{source_key}' is disabled. Skipping.")
            continue

        scraper_function_name = source_config.get("scraper_function_name")
        if not scraper_function_name:
            logger.warning(f"No 'scraper_function_name' defined for source: '{source_key}'. Skipping.")
            continue

        scraper_function = AVAILABLE_SCRAPER_FUNCTIONS.get(scraper_function_name)
        if not scraper_function:
            logger.error(f"Scraper function '{scraper_function_name}' for source '{source_key}' not found in AVAILABLE_SCRAPER_FUNCTIONS. Skipping.")
            continue

        logger.debug(f"Attempting to fetch news from '{source_key}' for '{symbol}' using function '{scraper_function_name}'...")
        
        scraper_args = [symbol]
        if "rss_url_template" in source_config and source_config["rss_url_template"] is not None:
            scraper_args.append(source_config["rss_url_template"])
        elif "base_url_template" in source_config and source_config["base_url_template"] is not None:
            scraper_args.append(source_config["base_url_template"])
        else: # מקרה שבו הפונקציה לא צריכה URL מההגדרות (למשל, אם ה-URL מקודד בה)
             logger.debug(f"No specific URL template found in config for '{source_key}', assuming function '{scraper_function_name}' handles its own URL or does not need one.")
        
        try:
            source_specific_headlines = scraper_function(*scraper_args) 

            if not source_specific_headlines:
                logger.info(f"No headlines returned from '{source_key}' for '{symbol}'.")
                continue

            headlines_added_from_this_source = 0
            for title, reported_source_name in source_specific_headlines[:DEFAULT_MAX_HEADLINES_PER_SOURCE]:
                cleaned_title = title.strip()
                title_lower = cleaned_title.lower()

                if cleaned_title and len(cleaned_title) >= MIN_HEADLINE_LENGTH and title_lower not in seen_titles_lower:
                    all_collected_headlines.append((cleaned_title, source_key))
                    seen_titles_lower.add(title_lower)
                    headlines_added_from_this_source += 1
                elif title_lower in seen_titles_lower:
                    logger.debug(f"Duplicate title (case-insensitive) skipped from '{source_key}': '{cleaned_title}'")
                elif cleaned_title:
                     logger.debug(f"Short title skipped from '{source_key}': '{cleaned_title}' (Length: {len(cleaned_title)})")

            if headlines_added_from_this_source > 0:
                logger.info(f"Added {headlines_added_from_this_source} unique headlines from '{source_key}' for '{symbol}'.")
            else:
                logger.info(f"No new unique headlines added from '{source_key}' for '{symbol}'.")
        
        except TypeError as te:
            logger.error(f"TypeError calling scraper function '{scraper_function_name}' for '{source_key}': {te}. Args: {scraper_args}. Check arguments and function signature.", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing source '{source_key}' for '{symbol}': {e}", exc_info=True)

        if len(all_collected_headlines) >= max_headlines_total:
            logger.info(f"Reached total headline limit of {max_headlines_total} for '{symbol}'. Stopping further fetching.")
            break

    if all_collected_headlines:
        logger.info(f"Total unique headlines aggregated for '{symbol}' across all sources: {len(all_collected_headlines)} (capped at {max_headlines_total}).")
    else:
        logger.info(f"No headlines aggregated for '{symbol}' across all sources.")

    return all_collected_headlines[:max_headlines_total]
