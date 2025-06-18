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
YAHOO_NEWS_URL_TEMPLATE = "https://finance.yahoo.com/quote/{symbol}/news"
OUTPUT_CSV_FILENAME = f"yahoo_scraped_pilot_{TEST_SYMBOL}.csv"

# --- ערכי העוגיות שסיפקת ---
EUCONSENT_VALUE = "CQTNA8AQTNA8AAOACBHEBvFoAP_gAEPgACiQKptB9G7WTXFneTp2YPskOYwX0VBJ4MAwBgCBAcABzBIUIBwGVmAzJEyIICACGAIAIGBBIABtGAhAQEAAYIAFAABIAEgAIBAAIGAAACAAAABACAAAAAAAAAAQgEAXMBQgmCYEBFoIQUhAggAgAQAAAAAEAIgBCAQAEAAAQAAACAAIACgAAgAAAAAAAAAEAFAIEAAAIAECAgPkdAAAAAAAAAAIAAYACAABAAAAAIKpgAkGhUQRFgQAhEIGEECAAQUBABQIAgAACBAAAATBAUIAwAVGAiAEAIAAAAAAAAAAABAAABAAhAAEAAQIAAAAAIAAgAIBAAACAAAAAAAAAAAAAAAAAAAAAAAAAGIBAggCAABBAAQUAAAAAgAAAAAAAAAIgACAAAAAAAAAAAAAAIgAAAAAAAAAAAAAAAAAAIEAAAIAAAAoDEFgAAAAAAAAAAAAAACAABAAAAAIAAA"
GUC_VALUE = "AQABCAFoVBBofkIfRgSY&s=AQAAAB405PQD&g=aFLHVw"
GUCS_VALUE = "AX9tHvLB"

# הרכבת מחרוזת העוגיות - נתחיל עם EuConsent ו-GUCS
# הוספתי גם את GUC למקרה ששלושתן יחד יעבדו טוב יותר.
# סדר העוגיות בדרך כלל לא קריטי, אבל לפעמים כן.
COOKIE_STRING = f"EuConsent={EUCONSENT_VALUE}; GUCS={GUCS_VALUE}; GUC={GUC_VALUE}"
# אם זה לא עובד, נוכל לנסות רק EuConsent ו-GUCS:
# COOKIE_STRING = f"EuConsent={EUCONSENT_VALUE}; GUCS={GUCS_VALUE}"
# או רק EuConsent:
# COOKIE_STRING = f"EuConsent={EUCONSENT_VALUE}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9', 
    'Connection': 'keep-alive',
    'Cookie': COOKIE_STRING 
}
# ------------------------------------

def scrape_yahoo_news_page(symbol: str) -> list[dict]:
    url = YAHOO_NEWS_URL_TEMPLATE.format(symbol=symbol) 
    logger.info(f"Attempting to scrape: {url} with custom cookies.")
    logger.debug(f"Using Cookies string: {HEADERS.get('Cookie', 'None')}")
    
    collected_articles = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=30) 
        logger.info(f"Response status code for {url}: {response.status_code}")
        
        # בדוק אם הכותרת של הדף היא עדיין דף ההסכמה
        # התאמתי את הבדיקה שתהיה רגישה פחות לאותיות גדולות/קטנות ותכסה גם אנגלית
        page_title_lower = ""
        if response.content: # ודא שיש תוכן לפני ניסיון לנתח אותו
            temp_soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
            if temp_soup.title and temp_soup.title.string:
                page_title_lower = temp_soup.title.string.lower()
        
        if "yahoo ist teil der yahoo-markenfamilie" in page_title_lower or \
           "yahoo is part of the yahoo family of brands" in page_title_lower or \
           "consent.yahoo.com" in response.url.lower(): # בדוק גם אם ה-URL הסופי הוא דף ההסכמה
            logger.error(f"Still getting the consent page for {symbol}, even with cookies. Cookies might be incorrect, insufficient, or the wrong ones.")
            logger.debug(f"Consent page URL: {response.url}")
            logger.debug(f"Consent page Title: {page_title_lower}")
            logger.debug(f"Consent page HTML sample (first 1000 chars) for {symbol}:\n{response.text[:1000]}")
            return [] 

        response.raise_for_status() 
        
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
        
        news_items = []
        # ניסיון 1: חיפוש ה-ul שמכיל את החדשות
        fin_stream_ul = soup.find('ul', id=lambda x: x and x.startswith('FinStream'))
        if fin_stream_ul:
            potential_items_v1 = fin_stream_ul.find_all('li', class_=lambda x: x and 'StreamItem' in x, recursive=False)
            if potential_items_v1:
                logger.debug(f"Found {len(potential_items_v1)} items using 'ul#FinStream... > li.StreamItem'")
                news_items.extend(potential_items_v1)
        
        if not news_items: # אם לא נמצאו עם ה-selector הראשון, נסה גישה רחבה יותר
            potential_items_v2 = soup.find_all('li', class_=lambda x: x and 'StreamItem' in x and 'QuoteNews' in x)
            if potential_items_v2:
                logger.debug(f"Found {len(potential_items_v2)} items using broader 'li.StreamItem.QuoteNews'")
                news_items.extend(potential_items_v2)

        if not news_items:
            logger.debug("No items from specific selectors, trying broader search for <a> tags with <h3>...")
            links_with_h3 = soup.select('a > h3') 
            if links_with_h3:
                 logger.debug(f"Found {len(links_with_h3)} <a><h3> candidates.")
                 news_items.extend([link.parent.parent for link in links_with_h3 if link.parent and link.parent.parent])


        if not news_items:
            logger.warning(f"No news items found on the page for {symbol} with any of the attempted selectors. Page structure might have changed or content is loaded differently.")
            logger.debug(f"Page HTML sample (first 5000 chars) for {symbol}:\n{soup.prettify()[:5000]}")
            return []

        logger.info(f"Found a total of {len(news_items)} potential news items for {symbol} using combined selectors.")

        processed_titles = set() 

        for item_idx, item in enumerate(news_items):
            title = "N/A"
            link = "N/A"
            source_name_on_page = "N/A"
            publish_date_str = "N/A"
            
            title_anchor = item.find('a', href=True) 
            if title_anchor:
                # חפש כותרת בתוך תגיות h3 או div עם class מתאים בתוך הקישור
                title_h3 = title_anchor.find('h3')
                if title_h3:
                    title = title_h3.get_text(strip=True)
                else: # נסה לקחת את הטקסט של הקישור עצמו אם אין h3
                    title = title_anchor.get_text(strip=True)
                
                link_raw = title_anchor.get('href', "N/A")
                if link_raw.startswith('/'):
                    link = f"https://finance.yahoo.com{link_raw}"
                elif link_raw.startswith('http'):
                    link = link_raw
            
            # אם לא מצאנו כותרת טובה מהקישור, נסה למצוא h3 כלשהו ב-item
            if not title or title == "N/A" or len(title) < 10: 
                h3_tag = item.find('h3') 
                if h3_tag:
                    title = h3_tag.get_text(strip=True)
            
            # חילוץ מקור ותאריך (זה החלק הכי שביר בד"כ)
            # המבנה יכול להשתנות, ננסה כמה אפשרויות
            meta_info_container = item.find('div', class_=lambda x: x and ('Fz(12px)' in x or 'Meta' in x or 'StreamSource' in x or 'C(#959595)' in x))
            if meta_info_container:
                spans = meta_info_container.find_all('span', recursive=False) 
                divs_for_source = meta_info_container.find_all('div', recursive=False) # לפעמים המקור ב-div

                if spans:
                    if len(spans) >= 1 and not source_name_on_page != "N/A": # אם עוד לא מצאנו מקור
                        source_name_on_page = spans[0].get_text(strip=True)
                    if len(spans) >= 2: 
                        publish_date_str = spans[-1].get_text(strip=True) # נניח שהאחרון הוא התאריך
                    elif len(spans) == 1: # אם יש רק אחד, זה יכול להיות תאריך או מקור
                        text_content = spans[0].get_text(strip=True)
                        if any(kw in text_content.lower() for kw in ['ago', 'yesterday', 'min', 'hour', 'today']) or \
                           any(month.lower() in text_content.lower() for month in ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']):
                            publish_date_str = text_content
                        elif source_name_on_page == "N/A": # אם זה לא נראה כמו תאריך, אולי זה המקור
                            source_name_on_page = text_content
                elif divs_for_source: # אם המקור/תאריך נמצאים ב-divs
                     if len(divs_for_source) >= 1 and source_name_on_page == "N/A":
                        source_name_on_page = divs_for_source[0].get_text(strip=True)
                     if len(divs_for_source) >=2:
                        publish_date_str = divs_for_source[-1].get_text(strip=True)


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
        # חשוב: בדוק אם response מוגדר לפני גישה אליו
        if 'response' in locals() and response is not None:
            logger.debug(f"Response content for HTTP error: {response.text[:500] if response.text else 'No response text'}")
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
