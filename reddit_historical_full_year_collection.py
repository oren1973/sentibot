import praw
import os
import pandas as pd
from datetime import datetime, timezone
import logging
import time

# --- הגדרות איסוף ---
# רשימת הטיקרים מהמסמך (בלי הבעייתיים מהורדת המחירים)
TICKERS_TO_SCRAPE = [
    "TSLA", "META", "NVDA", "AMD", "GME", "AMC", "PLTR", "COIN", "BB", "CVNA", 
    "SPCE", "LCID", "NIO", "XPEV", "RIVN", "MULN", "SOFI", "MARA", 
    "RIOT", "MSTR", "AI", "BBAI", "SOUN", "TLRY", "NVAX", "SAVA", "ENVX", 
    "EOSE", "ACHR", "CHPT", "SMCI", "UPST", "DKNG", "BYND", 
    "DNA", "SNDL"
]

# סאברדיטים לחיפוש (אפשר לקחת מ-settings.py אם הוא זמין)
SUBREDDITS_TO_SEARCH = ["wallstreetbets", "stocks", "StockMarket", "investing", "options"] 
# אם רוצים לייבא מ-settings:
# try:
# from settings import REDDIT_SUBREDDITS
#     SUBREDDITS_TO_SEARCH = REDDIT_SUBREDDITS
# except ImportError:
#     pass # השתמש ברשימה המקומית

SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER = 50  # כמה פוסטים לנסות לשלוף לכל היותר לכל טיקר בכל סאברדיט
SEARCH_TIME_FILTER = "year"                 # 'year' כדי לקבל פוסטים מהשנה האחרונה
OUTPUT_CSV_FILENAME = f"reddit_historical_data_1year_{datetime.now().strftime('%Y%m%d')}.csv"
MIN_POST_RELEVANCE_SCORE_FOR_BODY = 10 # ניקוד מינימלי לפוסט כדי שניטרח לשלוף את גופו (אם הוא ארוך)

# --- ניסיון לייבא פונקציות עזר ---
EMAIL_SENDER_AVAILABLE = False
try:
    from email_sender import send_email 
    from settings import setup_logger 
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("RedditHistoricalFull", level=logging.INFO) # נתחיל עם INFO, אפשר לשנות ל-DEBUG אם צריך
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("RedditHistoricalFull_Fallback")
    logger.warning("Could not import from email_sender or settings. Email functionality will be disabled. Using basic logger.")

# -- קריאת פרטי API של Reddit ממשתני סביבה --
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SentibotDataCollection/0.3 by YourRedditUsername") 

reddit_client_instance = None 
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    logger.critical("Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET) are not set.")
else:
    if not REDDIT_USER_AGENT or "YourRedditUsername" in REDDIT_USER_AGENT:
        logger.warning(f"Reddit User-Agent may be generic ('{REDDIT_USER_AGENT}'). Set a unique REDDIT_USER_AGENT.")
    try:
        logger.info(f"Initializing PRAW client with User-Agent: {REDDIT_USER_AGENT}")
        reddit_client_instance = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            read_only=True
        )
        logger.info("PRAW client initialized (read-only status: {}).".format(reddit_client_instance.read_only))
    except Exception as e:
        logger.critical(f"Failed to initialize PRAW Reddit client: {e}", exc_info=True)
        reddit_client_instance = None

def fetch_posts_for_ticker_and_subreddit(symbol: str, subreddit_name: str, limit: int, time_filter: str) -> list[dict]:
    if reddit_client_instance is None:
        return []

    collected_data = []
    search_query = f'"{symbol}"' # חיפוש הסמל במרכאות
    
    logger.info(f"  Fetching for '{symbol}' in r/{subreddit_name} (Query: '{search_query}', Limit: {limit}, Time: {time_filter})")

    try:
        subreddit = reddit_client_instance.subreddit(subreddit_name)
        # נשתמש ב-sort='relevance' כדי לנסות לקבל תוצאות יותר רלוונטיות לשאילתה,
        # למרות שזה עשוי להיות פחות טוב לכיסוי היסטורי מאשר 'top' או 'new'.
        # אפשר להתנסות עם sort='top' או sort='new' גם.
        submissions = subreddit.search(query=search_query, sort='relevance', time_filter=time_filter, limit=limit)
        
        processed_submissions = 0
        for submission in submissions:
            processed_submissions += 1
            if submission.stickied or submission.over_18:
                continue

            post_title = submission.title.strip()
            
            # נשלוף גוף הפוסט רק אם יש כותרת או שהניקוד גבוה יחסית (כדי לחסוך בקשות אם הגוף ארוך)
            post_body = ""
            if post_title or submission.score > MIN_POST_RELEVANCE_SCORE_FOR_BODY:
                 post_body = submission.selftext.strip() if submission.selftext else ""
            
            if not post_title and not post_body: # דלג אם אין כותרת ואין גוף
                continue

            created_iso = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat()

            collected_data.append({
                "symbol_searched": symbol,
                "subreddit": subreddit_name,
                "post_id": submission.id,
                "created_utc_iso": created_iso,
                "title": post_title,
                "body": post_body,
                "url": submission.url,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "flair": str(submission.link_flair_text)
            })
        logger.info(f"    r/{subreddit_name}: Processed {processed_submissions} PRAW submissions, collected {len(collected_data)} valid posts.")
    except Exception as e:
        logger.error(f"  Error fetching from r/{subreddit_name} for '{symbol}': {e}", exc_info=False) # exc_info=False כדי לא להעמיס על הלוג
    
    return collected_data

if __name__ == "__main__":
    if not reddit_client_instance:
        logger.critical("Reddit client not initialized. Aborting script.")
        exit()

    logger.info(f"--- Starting Reddit Historical Data Collection for {len(TICKERS_TO_SCRAPE)} tickers ---")
    logger.info(f"Subreddits to search: {', '.join(SUBREDDITS_TO_SEARCH)}")
    logger.info(f"Time filter: '{SEARCH_TIME_FILTER}', Limit per ticker per subreddit: {SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER}")

    all_collected_posts_list = []
    total_posts_collected = 0

    for i, ticker in enumerate(TICKERS_TO_SCRAPE):
        logger.info(f"\nProcessing Ticker {i+1}/{len(TICKERS_TO_SCRAPE)}: {ticker}")
        posts_for_this_ticker = []
        for subreddit_name in SUBREDDITS_TO_SEARCH:
            # השהיה קטנה בין בקשות לסאברדיטים שונים (או לטיקרים שונים)
            # כדי להיות נחמדים ל-API של Reddit
            time.sleep(1) # שנייה אחת השהיה
            
            posts = fetch_posts_for_ticker_and_subreddit(
                symbol=ticker,
                subreddit_name=subreddit_name,
                limit=SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER,
                time_filter=SEARCH_TIME_FILTER
            )
            if posts:
                posts_for_this_ticker.extend(posts)
        
        if posts_for_this_ticker:
            all_collected_posts_list.extend(posts_for_this_ticker)
            total_posts_collected += len(posts_for_this_ticker)
            logger.info(f"  Collected {len(posts_for_this_ticker)} posts for {ticker} across all subreddits.")
        else:
            logger.info(f"  No posts collected for {ticker} across all subreddits.")
    
    logger.info(f"\n--- Finished Reddit Data Collection ---")
    logger.info(f"Total posts collected for all tickers: {total_posts_collected}")

    if all_collected_posts_list:
        final_df = pd.DataFrame(all_collected_posts_list)
        if not final_df.empty:
            final_df['created_utc_iso'] = pd.to_datetime(final_df['created_utc_iso'])
            final_df.sort_values(by=['symbol_searched', 'created_utc_iso'], ascending=[True, True], inplace=True)
            
            try:
                final_df.to_csv(OUTPUT_CSV_FILENAME, index=False, encoding='utf-8-sig')
                logger.info(f"All Reddit historical data saved to: {OUTPUT_CSV_FILENAME}")
                logger.info(f"DataFrame shape: {final_df.shape}")

                if EMAIL_SENDER_AVAILABLE and os.path.exists(OUTPUT_CSV_FILENAME):
                    email_subject = f"Sentibot - Reddit Historical Data ({SEARCH_TIME_FILTER} - {datetime.now().strftime('%Y-%m-%d')})"
                    email_body = (
                        f"Reddit historical data collection finished.\n"
                        f"Tickers processed: {len(TICKERS_TO_SCRAPE)}\n"
                        f"Subreddits searched: {', '.join(SUBREDDITS_TO_SEARCH)}\n"
                        f"Time filter: '{SEARCH_TIME_FILTER}'\n"
                        f"Limit per ticker/sub: {SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER}\n\n"
                        f"Total posts collected: {total_posts_collected}\n"
                        f"The data is attached as '{OUTPUT_CSV_FILENAME}'.\n\n"
                        f"Sentibot"
                    )
                    
                    email_sent = send_email(
                        subject=email_subject,
                        body=email_body,
                        attachment_paths=[OUTPUT_CSV_FILENAME]
                    )
                    if email_sent:
                        logger.info(f"Email with Reddit historical data CSV sent successfully.")
                    else:
                        logger.error(f"Failed to send email with Reddit historical data CSV.")
                elif not EMAIL_SENDER_AVAILABLE:
                    logger.warning("Email sending is not available for Reddit data.")
                elif not os.path.exists(OUTPUT_CSV_FILENAME):
                    logger.warning(f"Output file {OUTPUT_CSV_FILENAME} not found for email for Reddit data.")
            except Exception as e_save:
                logger.error(f"Error saving Reddit data to CSV or sending email: {e_save}", exc_info=True)
        else:
            logger.info("Final DataFrame for Reddit data is empty. No CSV created.")
    else:
        logger.info("No posts collected at all. No CSV created.")
        
    logger.info(f"--- Reddit Historical Data Collection Script Finished ---")
