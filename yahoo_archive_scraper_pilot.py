import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging # הוספתי

# הגדרת לוגר בסיסי לסקריפט הפיילוト
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("YahooArchiveScraperPilot")

# סמל לבדיקה
TEST_SYMBOL = "AAPL" # אפשר לשנות למניה אחרת מהרשימה שלך
YAHOO_NEWS_URL_TEMPLATE = "https://finance.yahoo.com/quote/{symbol}/news?p={symbol}"

# User-Agent כדי לדמות דפדפן
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_yahoo_news_page(symbol: str) -> list[dict]:
    url = YAHOO_NEWS_URL_TEMPLATE.replace("{symbol}", symbol)
    logger.info(f"Attempting to scrape: {url}")
    
    collected_articles = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status() # יעלה שגיאה אם הסטטוס הוא 4xx או 5xx
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ננסה למצוא את הפריטים החדשותיים. זה ידרוש בדיקה של מבנה ה-HTML של יאהו.
        # זו רק דוגמה ל-selector, ייתכן שהוא לא נכון ויצטרך התאמה.
        # בדרך כלל, פריטי חדשות נמצאים בתוך תגיות <li> או <div> עם class מסוים.
        # ונחפש קישור <a> עם כותרת בתוכו, ומידע על המקור והתאריך.
        
        # ננסה למצוא את ה-stream items, שהם לרוב מכילים את החדשות
        # המבנה של יאהו משתנה, אז זה יכול להיות שביר
        news_items = soup.find_all('li', class_=lambda x: x and 'StreamItem' in x and 'QuoteNews' in x)
        # אם זה לא עובד, נסה selectors רחבים יותר או בדוק את ה-HTML הנוכחי.
        # news_items = soup.select('div.Cf > ul > li > div > div') # דוגמה ל-selector ישן יותר
        # news_items = soup.find_all('div', class_='Ov(h) Pend(44px) Pstart(25px)') # עוד דוגמה

        if not news_items:
            logger.warning(f"No news items found on the page for {symbol} with current selectors. The page structure might have changed.")
            # נסה להדפיס חלק מה-HTML כדי שנוכל לבדוק
            # logger.debug(f"Page HTML sample (first 2000 chars):\n{soup.prettify()[:2000]}")
            return []

        logger.info(f"Found {len(news_items)} potential news items for {symbol}.")

        for item in news_items:
            title = "N/A"
            link = "N/A"
            source_name = "N/A"
            publish_date_str = "N/A"
            
            # חילוץ כותרת וקישור
            title_tag = item.find('h3') # או כל תגית אחרת שמכילה את הכותרת
            if title_tag and title_tag.find('a'):
                title_anchor = title_tag.find('a')
                title = title_anchor.get_text(strip=True)
                link = title_anchor.get('href', "N/A")
                if not link.startswith('http'): # אם זה קישור יחסי
                    link = f"https://finance.yahoo.com{link}"

            # חילוץ מקור ותאריך (זה יכול להיות מסובך כי המבנה משתנה)
            # נחפש div שמכיל את שם המקור ואת התאריך
            provider_div = item.find('div', class_=lambda x: x and 'StreamSource' in x) # דוגמה
            if provider_div:
                source_span = provider_div.find('span') # או div
                if source_span:
                    source_name = source_span.get_text(strip=True)
                
                time_tag = provider_div.find('span', class_=lambda x: x and 'time' in x.lower()) # או תגית time
                if time_tag:
                    publish_date_str = time_tag.get_text(strip=True) 
                    # נצטרך לנתח את מחרוזת התאריך הזו, היא יכולה להיות "2 hours ago", "Jun 18", "Yesterday"
                    # או תאריך מלא. זה ידרוש לוגיקה נוספת לניתוח.

            if title != "N/A" and title: # ודא שיש כותרת
                collected_articles.append({
                    "symbol": symbol,
                    "title": title,
                    "link": link,
                    "source_name_on_page": source_name, # המקור כפי שהוא מופיע בדף
                    "publish_date_str": publish_date_str, # התאריך כפי שהוא מופיע בדף
                    "scrape_timestamp": datetime.now().isoformat()
                })
                logger.debug(f"  Collected: '{title}' from '{source_name}' dated '{publish_date_str}'")

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
        print("\n--- Scraped Articles DataFrame ---")
        print(df.to_string())
        
        # שמירת הפלט לקובץ CSV לבדיקה
        output_csv_name = f"yahoo_scraped_pilot_{TEST_SYMBOL}.csv"
        df.to_csv(output_csv_name, index=False, encoding='utf-8-sig')
        logger.info(f"Scraped data saved to {output_csv_name}")
    else:
        logger.info(f"No articles were scraped for {TEST_SYMBOL}.")
        
    logger.info(f"--- Yahoo Finance Archive Scraper Pilot Finished ---")
