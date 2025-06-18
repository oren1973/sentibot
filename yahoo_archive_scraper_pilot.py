import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging 
import os 

try:
    from email_sender import send_email 
    from settings import setup_logger 
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("YahooArchiveScraperPilot", level=logging.DEBUG) 
except ImportError:
    EMAIL_SENDER_AVAILABLE = False
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("YahooArchiveScraperPilot_Fallback")
    logger.warning("Could not import from email_sender or settings for pilot. Email functionality will be disabled if run in cloud without env vars.")

TEST_SYMBOL = "AAPL" 
# ודא שאין לוכסן בסוף התבנית
YAHOO_NEWS_URL_TEMPLATE = "https://finance.yahoo.com/quote/{symbol}/news" # <--- ה-URL הנכון
OUTPUT_CSV_FILENAME = f"yahoo_scraped_pilot_{TEST_SYMBOL}.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
}

def scrape_yahoo_news_page(symbol: str) -> list[dict]:
    url = YAHOO_NEWS_URL_TEMPLATE.format(symbol=symbol) # שימוש ב-format() לבניית ה-URL
    logger.info(f"Attempting to scrape: {url}")
    
    collected_articles = []

    try:
        # נסה עם verify=False אם יש בעיות SSL, למרות שלא סביר כאן
        response = requests.get(url, headers=HEADERS, timeout=30) # הגדלתי timeout
        logger.info(f"Response status code for {url}: {response.status_code}")
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- ניסיונות מרובים למצוא פריטי חדשות ---
        news_items = []
        
        # ניסיון 1: Selector שהיה נפוץ בעבר (קונטיינר FinStream)
        # פריטים נמצאים בתוך <li class="js-stream-content Pos(r)">
        potential_items_v1 = soup.select('div#Fin-Stream ul > li.js-stream-content')
        if potential_items_v1:
            logger.debug(f"Found {len(potential_items_v1)} items using 'div#Fin-Stream ul > li.js-stream-content'")
            news_items.extend(potential_items_v1)

        # ניסיון 2: Selector שהופיע בלוגיקה הקודמת שלך (יותר כללי)
        if not news_items:
            potential_items_v2 = soup.find_all('li', class_=lambda x: x and 'StreamItem' in x and 'QuoteNews' in x)
            if potential_items_v2:
                logger.debug(f"Found {len(potential_items_v2)} items using 'li.StreamItem.QuoteNews'")
                news_items.extend(potential_items_v2)

        # ניסיון 3: חיפוש כללי יותר של קישורים עם כותרות בתוכם
        if not news_items:
            logger.debug("No items from specific selectors, trying broader search for <a> tags with <h3>...")
            links_with_h3 = soup.select('a > h3') # הרבה פעמים כותרות הן h3 בתוך a
            if links_with_h3:
                 logger.debug(f"Found {len(links_with_h3)} <a><h3> candidates.")
                 # נצטרך לעלות ל-parent כדי לקבל את כל ה-item
                 news_items.extend([link.parent.parent for link in links_with_h3 if link.parent and link.parent.parent])


        if not news_items:
            logger.warning(f"No news items found on the page for {symbol} with any of the attempted selectors. Page structure might have changed or content is loaded differently.")
            logger.debug(f"Page HTML sample (first 5000 chars) for {symbol}:\n{soup.prettify()[:5000]}")
            return []

        logger.info(f"Found a total of {len(news_items)} potential news items for {symbol} using combined selectors.")

        processed_titles = set() # למניעת כפילויות אם selectors שונים תופסים אותו פריט

        for item_idx, item in enumerate(news_items):
            title = "N/A"
            link = "N/A"
            source_name_on_page = "N/A"
            publish_date_str = "N/A"
            
            # חילוץ כותרת וקישור - נסה מספר דרכים
            title_anchor = item.find('a', href=True) # חפש את הקישור הראשי בתוך ה-item
            if title_anchor:
                title_candidate_h3 = title_anchor.find('h3')
                if title_candidate_h3:
                    title = title_candidate_h3.get_text(strip=True)
                else: # אם אין h3, נסה לקחת את הטקסט של הקישור עצמו
                    title = title_anchor.get_text(strip=True)
                
                link_raw = title_anchor.get('href', "N/A")
                if link_raw.startswith('/'):
                    link = f"https://finance.yahoo.com{link_raw}"
                elif link_raw.startswith('http'):
                    link = link_raw
            
            if not title or title == "N/A" or len(title) < 10: # אם לא מצאנו כותרת טובה מהקישור
                h3_tag = item.find('h3') # נסה למצוא h3 כלשהו
                if h3_tag:
                    title = h3_tag.get_text(strip=True)
                # אפשר להוסיף עוד ניסיונות אם צריך

            # חילוץ מקור ותאריך
            # המבנה יכול להיות: <div class="..."><span class="source">Reuters</span><span class="time">2 hours ago</span></div>
            # או <div class="..."><span class="provider">Yahoo Finance</span><span>June 18, 2025</span></div>
            meta_info_container = item.find('div', class_=lambda x: x and ('Fz(12px)' in x or 'Meta' in x or 'StreamSource' in x))
            if meta_info_container:
                spans = meta_info_container.find_all('span', recursive=False) # רק ילדים ישירים
                if spans:
                    if len(spans) >= 1:
                        source_name_on_page = spans[0].get_text(strip=True)
                    if len(spans) >= 2: # נניח שהתאריך הוא השני אם יש שניים
                        publish_date_str = spans[1].get_text(strip=True)
                    elif len(spans) == 1: # אם יש רק אחד, זה יכול להיות תאריך או מקור
                        # ננסה לזהות אם זה נראה כמו תאריך
                        text_content = spans[0].get_text(strip=True)
                        if any(kw in text_content.lower() for kw in ['ago', 'yesterday', 'min', 'hour']) or \
                           any(month in text_content for month in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']):
                            publish_date_str = text_content
                        else: # נניח שזה המקור
                            source_name_on_page = text_content


            if title and title != "N/A" and len(title) >= 10 and title.lower() not in processed_titles:
                processed_titles.add(title.lower())
                collected_articles.append({
                    "symbol_scraped_for": symbol,
                    "title": title,
                    "link": link,
                    "source_name_on_page": source_name_on_page,
                    "publish_date_str": publish_date_str, 
                    "scrape_timestamp": datetime.now().isoformat()
                })
                logger.debug(f"  Collected ({item_idx+1}): '{title[:80]}' from '{source_name_on_page}' dated '{publish_date_str}'")
            elif title and title != "N/A":
                 logger.debug(f"  Skipped (short or duplicate) ({item_idx+1}): '{title[:80]}'")


    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred for {symbol} at {url}: {http_err}")
        logger.debug(f"Response content for HTTP error: {response.text[:500] if response else 'No response'}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred for {symbol} at {url}: {req_err}")
    except Exception as e:
        logger.error(f"An unexpected error occurred for {symbol} at {url}: {e}", exc_info=True)
        
    return collected_articles

if __name__ == "__main__":
    logger.info(f"--- Starting Yahoo Finance Archive Scraper Pilot for symbol: {TEST_SYMBOL} ---")
    
    articles = scrape_yahoo_news_page(TEST_SYMBOL)
    
    if articles:
        logger.info(f"Successfully scraped {len(articles)} articles for {TEST_SYMBOL}.")
        df = pd.DataFrame(articles)
        
        logger.info("\n--- Scraped Articles DataFrame (first 5) ---")
        for index, row in df.head().iterrows(): 
            logger.info(f"Title: {row['title']}, Source: {row['source_name_on_page']}, Date String: {row['publish_date_str']}")
        
        try:
            df.to_csv(OUTPUT_CSV_FILENAME, index=False, encoding='utf-8-sig')
            logger.info(f"Scraped data saved to {OUTPUT_CSV_FILENAME}")

            if EMAIL_SENDER_AVAILABLE and os.path.exists(OUTPUT_CSV_FILENAME):
                email_subject = f"Sentibot - Yahoo Archive Scraper Pilot Results ({TEST_SYMBOL})"
                email_body = (
                    f"Yahoo Archive Scraper pilot finished for symbol {TEST_SYMBOL}.\n"
                    f"Scraped {len(articles)} articles.\n\n"
                    f"The data is attached as '{OUTPUT_CSV_FILENAME}'.\n\n"
                    f"Sentibot"
                )
                
                email_sent = send_email(
                    subject=email_subject,
                    body=email_body,
                    attachment_paths=[OUTPUT_CSV_FILENAME] 
                )

                if email_sent:
                    logger.info(f"Email with pilot results CSV sent successfully.")
                else:
                    logger.error(f"Failed to send email with pilot results CSV.")
            elif not EMAIL_SENDER_AVAILABLE:
                 logger.warning("Email sending is not available (could not import email_sender or settings).")
            elif not os.path.exists(OUTPUT_CSV_FILENAME):
                 logger.warning(f"Output file {OUTPUT_CSV_FILENAME} not found for email attachment.")
            
        except Exception as e_save_email:
            logger.error(f"Error saving CSV or sending email: {e_save_email}")
            
    else:
        logger.info(f"No articles were scraped for {TEST_SYMBOL}.")
        
    logger.info(f"--- Yahoo Finance Archive Scraper Pilot Finished ---")
