import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging
import os # נוסף עבור בדיקת קיום קובץ ושליפת שם קובץ

# נניח ש-email_sender.py ו-settings.py זמינים לייבוא
try:
    from email_sender import send_email
    from settings import setup_logger # אם אתה רוצה להשתמש בלוגר המרכזי שלך
    EMAIL_SENDER_AVAILABLE = True
    # אפשר להשתמש ב-setup_logger אם הוא מיובא בהצלחה
    logger = setup_logger("YahooArchiveScraperPilot", level=logging.DEBUG) # DEBUG כדי לראות יותר פרטים
except ImportError:
    EMAIL_SENDER_AVAILABLE = False
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("YahooArchiveScraperPilot_Fallback")
    logger.warning("Could not import from email_sender or settings for pilot. Email functionality will be disabled if run in cloud without env vars.")


# סמל לבדיקה
TEST_SYMBOL = "AAPL" 
YAHOO_NEWS_URL_TEMPLATE = "https://finance.yahoo.com/quote/{symbol}/news?p={symbol}"
OUTPUT_CSV_FILENAME = f"yahoo_scraped_pilot_{TEST_SYMBOL}.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_yahoo_news_page(symbol: str) -> list[dict]:
    url = YAHOO_NEWS_URL_TEMPLATE.replace("{symbol}", symbol)
    logger.info(f"Attempting to scrape: {url}")
    
    collected_articles = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # selectors - אלה יצטרכו כנראה התאמה כי מבנה האתר משתנה
        news_items = soup.find_all('li', class_=lambda x: x and 'StreamItem' in x and 'QuoteNews' in x)
        # אפשר לנסות selectors נוספים אם הראשון לא עובד:
        # if not news_items:
        #    news_items = soup.select('div.Cf > ul > li > div > div') 

        if not news_items:
            logger.warning(f"No news items found on the page for {symbol} with current selectors. Page structure might have changed.")
            logger.debug(f"Page HTML sample (first 2000 chars) for {symbol}:\n{soup.prettify()[:2000]}")
            return []

        logger.info(f"Found {len(news_items)} potential news items for {symbol}.")

        for item in news_items:
            title = "N/A"
            link = "N/A"
            source_name_on_page = "N/A" # המקור כפי שמופיע באתר יאהו
            publish_date_str = "N/A"
            
            title_tag_h3 = item.find('h3')
            title_anchor = None
            if title_tag_h3 and title_tag_h3.find('a'):
                title_anchor = title_tag_h3.find('a')
            
            if title_anchor:
                title = title_anchor.get_text(strip=True)
                link_raw = title_anchor.get('href', "N/A")
                # ודא שהקישור הוא אבסולוטי
                if link_raw.startswith('/'):
                    link = f"https://finance.yahoo.com{link_raw}"
                else:
                    link = link_raw
            else: # נסה למצוא קישורים אחרים אם המבנה שונה
                other_link = item.find('a', href=True)
                if other_link:
                    title_candidate = other_link.get_text(strip=True)
                    if len(title_candidate) > 15 : # נניח שכותרת צריכה להיות באורך מסוים
                         title = title_candidate
                         link_raw = other_link['href']
                         if link_raw.startswith('/'):
                            link = f"https://finance.yahoo.com{link_raw}"
                         else:
                            link = link_raw
                
            provider_div = item.find('div', class_=lambda x: x and 'StreamSource' in x) 
            if provider_div:
                source_span = provider_div.find_all('span') # יכולים להיות מספר spans
                if source_span and len(source_span) > 0:
                    source_name_on_page = source_span[0].get_text(strip=True) # נניח שהראשון הוא המקור
                if source_span and len(source_span) > 1: # נניח שהשני הוא התאריך
                    publish_date_str = source_span[-1].get_text(strip=True) # נסה לקחת את האחרון

            if title != "N/A" and title:
                collected_articles.append({
                    "symbol_scraped_for": symbol,
                    "title": title,
                    "link": link,
                    "source_name_on_page": source_name_on_page,
                    "publish_date_str": publish_date_str, 
                    "scrape_timestamp": datetime.now().isoformat()
                })
                logger.debug(f"  Collected: '{title[:80]}' from '{source_name_on_page}' dated '{publish_date_str}'")

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred for {symbol}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred for {symbol}: {req_err}")
    except Exception as e:
        logger.error(f"An unexpected error occurred for {symbol}: {e}", exc_info=True)
        
    return collected_articles

if __name__ == "__main__":
    logger.info(f"--- Starting Yahoo Finance Archive Scraper Pilot for symbol: {TEST_SYMBOL} ---")
    
    articles = scrape_yahoo_news_page(TEST_SYMBOL)
    
    if articles:
        logger.info(f"Successfully scraped {len(articles)} articles for {TEST_SYMBOL}.")
        df = pd.DataFrame(articles)
        
        # הדפסת התוצאות ללוג (אפשר גם ל-print אם רוצים לראות ב-shell)
        logger.info("\n--- Scraped Articles DataFrame ---")
        for index, row in df.iterrows():
            logger.info(f"Title: {row['title']}, Source: {row['source_name_on_page']}, Date String: {row['publish_date_str']}")
        
        try:
            df.to_csv(OUTPUT_CSV_FILENAME, index=False, encoding='utf-8-sig')
            logger.info(f"Scraped data saved to {OUTPUT_CSV_FILENAME}")

            # --- שליחת הקובץ במייל ---
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
            # --- סוף שליחת המייל ---

        except Exception as e_save_email:
            logger.error(f"Error saving CSV or sending email: {e_save_email}")
            
    else:
        logger.info(f"No articles were scraped for {TEST_SYMBOL}.")
        
    logger.info(f"--- Yahoo Finance Archive Scraper Pilot Finished ---")
