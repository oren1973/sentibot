# marketwatch_scraper.py
import requests
from bs4 import BeautifulSoup
from settings import setup_logger, MIN_HEADLINE_LENGTH

logger = setup_logger(__name__)

def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned

def fetch_marketwatch_titles(symbol: str, base_url_template: str) -> list[tuple[str, str]]:
    source_name = "MarketWatch"
    headlines_data = []
    
    if not base_url_template:
        logger.error(f"Base URL template not provided for {source_name}. Cannot fetch news for {symbol}.")
        return []

    target_url = base_url_template.replace("{symbol_lower}", symbol.lower())
    
    headers = { # נסה עם User-Agent זה, אם עדיין נחסם, נסה אחר או נטרל זמנית
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }

    logger.info(f"Fetching news for '{symbol}' from {source_name} via scraping URL: {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=20) 
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        potential_headlines_elements = soup.select('a h3[class*="headline"], a h4[class*="headline"], a h3[class*="title"], a h4[class*="title"], div.article__content > a > h3.article__title')
        
        if not potential_headlines_elements:
            logger.debug(f"Initial selectors found no elements for '{symbol}' on {source_name}. Trying broader selectors.")
            potential_headlines_elements = soup.find_all(['h3', 'h4'], class_=lambda c: c and ('headline' in c or 'title' in c))

        if not potential_headlines_elements:
            logger.info(f"No headline elements found on {source_name} page for '{symbol}'. (URL: {target_url})")
            return []
            
        logger.debug(f"Found {len(potential_headlines_elements)} potential headline elements for '{symbol}' on {source_name}.")

        titles_added_count = 0
        for element in potential_headlines_elements:
            raw_title_text = element.get_text(strip=False) 
            cleaned_title = _clean_text(raw_title_text)
            
            if cleaned_title and len(cleaned_title) >= MIN_HEADLINE_LENGTH:
                headlines_data.append((cleaned_title, source_name))
                titles_added_count += 1
                if titles_added_count >= 10: 
                    logger.debug(f"Reached limit of {titles_added_count} headlines for '{symbol}' from {source_name}.")
                    break 
            elif cleaned_title:
                logger.debug(f"Skipping short/empty cleaned title from {source_name} for '{symbol}': '{cleaned_title}' (Original: '{raw_title_text[:50]}...')")
        
        logger.info(f"Successfully extracted {len(headlines_data)} headlines for '{symbol}' from {source_name}.")

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching from {source_name} for '{symbol}': {http_err} (URL: {target_url})")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during requests to {source_name} for '{symbol}': {req_err} (URL: {target_url})", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for '{symbol}': {e} (URL: {target_url})", exc_info=True)
        
    return headlines_data
