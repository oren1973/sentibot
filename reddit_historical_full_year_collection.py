import praw
import os
import pandas as pd
from datetime import datetime, timezone
import logging
import time

# --- הגדרות איסוף ---
TICKERS_TO_SCRAPE = [
    "TSLA", "META", "NVDA", "AMD", "GME", "AMC", "PLTR", "COIN", "BB", "CVNA", 
    "SPCE", "LCID", "NIO", "XPEV", "RIVN", "MULN", "SOFI", "MARA", 
    "RIOT", "MSTR", "AI", "BBAI", "SOUN", "TLRY", "NVAX", "SAVA", "ENVX", 
    "EOSE", "ACHR", "CHPT", "SMCI", "UPST", "DKNG", "BYND", 
    "DNA", "SNDL"
]

SUBREDDITS_TO_SEARCH = ["wallstreetbets", "stocks", "StockMarket", "investing", "options"] 

# הגדלנו את המגבלה, אבל נהיה זהירים עם קצב הבקשות
SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER = 100 # ננסה לאסוף עד 100 פוסטים לכל שילוב
SEARCH_TIME_FILTER = "year"                 
OUTPUT_CSV_FILENAME = f"reddit_historical_data_1year_limit{SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER}_{datetime.now().strftime('%Y%m%d')}.csv"
MIN_POST_RELEVANCE_SCORE_FOR_BODY = 10 
REQUEST_DELAY_SECONDS = 2 # השהיה של 2 שניות בין כל קריאת API ל-Reddit (חשוב!)

# --- ניסיון לייבא פונקציות עזר ---
EMAIL_SENDER_AVAILABLE = False
try:
    from email_sender import send_email 
    from settings import setup_logger 
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("RedditHistoricalFull", level=logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("RedditHistoricalFull_Fallback")
    logger.warning("Could not import from email_sender or settings. Email functionality will be disabled. Using basic logger.")

# -- קריאת פרטי API של Reddit ממשתני סביבה --
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SentibotDataCollection/0.4 by YourRedditUsername") # עדכנתי גרסה לדוגמה

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

def fetch_posts_for_ticker_and_subreddit(symbol: str, 
                                 subreddit_name: str, 
                                 limit: int, 
                                 time_filter: str,
                                 min_body_len: int = 10) -> list[dict]:
    if reddit_client_instance is None:
        return []

    collected_data = []
    search_query = f'"{symbol}"' 
    
    logger.info(f"  Fetching for '{symbol}' in r/{subreddit_name} (Query: '{search_query}', Limit: {limit}, Time: {time_filter})")

    try:
        subreddit = reddit_client_instance.subreddit(subreddit_name)
        # נשאר עם sort='relevance' כדי לנסות לקבל תוצאות יותר ממוקדות לשאילתה
        submissions = subreddit.search(query=search_query, sort='relevance', time_filter=time_filter, limit=limit, syntax='lucene') # lucene יכול לשפר חיפוש עם מרכאות
        
        processed_submissions = 0
        for submission in submissions:
            processed_submissions += 1
            if submission.stickied or submission.over_18:
                logger.debug(f"    Skipping stickied/over_18 post ID {submission.id}")
                continue

            post_title = submission.title.strip()
            post_body = ""
            # נשלוף גוף רק אם הכותרת רלוונטית או הניקוד גבוה, כדי לחסוך גישות אם לא צריך
            # הפעם נשלוף תמיד כי אנחנו רוצים את המידע לניתוח
            if submission.selftext:
                 post_body = submission.selftext.strip()
            
            if not post_title and (not post_body or len(post_body) < min_body_len) :
                logger.debug(f"    Skipping post ID {submission.id} due to empty title and short/empty body.")
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
                "flair": str(submission.link_flair_text) if submission.link_flair_text else None # טיפול במקרה שאין פלייר
            })
            # נרשום ללוג רק חלק מהפוסטים כדי לא להעמיס, או ברמת DEBUG
            if len(collected_data) % 10 == 0 or processed_submissions <= 5: # כל 10 פוסטים או 5 הראשונים
                 logger.debug(f"    Collected post ({len(collected_data)} of {processed_submissions} processed): '{post_title[:70]}...' (Date: {created_iso})")
        
        logger.info(f"    r/{subreddit_name}: Processed {processed_submissions} PRAW submissions, collected {len(collected_data)} valid posts for '{symbol}'.")
    except Exception as e:
        logger.error(f"  Error fetching from r/{subreddit_name} for '{symbol}': {e}", exc_info=False) 
    
    return collected_data

if __name__ == "__main__":
    if not reddit_client_instance:
        logger.critical("Reddit client not initialized. Aborting script.")
        exit()

    logger.info(f"--- Starting Reddit Historical Data Collection for {len(TICKERS_TO_SCRAPE)} tickers ---")
    logger.info(f"Subreddits to search: {', '.join(SUBREDDITS_TO_SEARCH)}")
    logger.info(f"Time filter: '{SEARCH_TIME_FILTER}', Limit per ticker per subreddit: {SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER}")
    logger.info(f"Delay between API calls: {REQUEST_DELAY_SECONDS} seconds.")

    all_collected_posts_list = []
    total_posts_collected_overall = 0

    for i, ticker in enumerate(TICKERS_TO_SCRAPE):
        logger.info(f"\nProcessing Ticker {i+1}/{len(TICKERS_TO_SCRAPE)}: {ticker}")
        posts_for_this_ticker_session = 0
        for subreddit_name in SUBREDDITS_TO_SEARCH:
            # השהיה *לפני* כל קריאה ל-API
            logger.debug(f"    Waiting {REQUEST_DELAY_SECONDS}s before querying r/{subreddit_name} for {ticker}...")
            time.sleep(REQUEST_DELAY_SECONDS) 
            
            posts = fetch_posts_for_ticker_and_subreddit(
                symbol=ticker,
                subreddit_name=subreddit_name,
                limit=SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER,
                time_filter=SEARCH_TIME_FILTER
            )
            if posts:
                all_collected_posts_list.extend(posts)
                posts_for_this_ticker_session += len(posts)
        
        if posts_for_this_ticker_session > 0:
            total_posts_collected_overall += posts_for_this_ticker_session
            logger.info(f"  Collected a total of {posts_for_this_ticker_session} posts for {ticker} across all searched subreddits this session.")
        else:
            logger.info(f"  No posts collected for {ticker} across all searched subreddits this session.")
    
    logger.info(f"\n--- Finished Reddit Data Collection ---")
    logger.info(f"Total posts collected overall for all tickers: {total_posts_collected_overall}")

    if all_collected_posts_list:
        final_df = pd.DataFrame(all_collected_posts_list)
        if not final_df.empty:
            final_df['created_utc_iso'] = pd.to_datetime(final_df['created_utc_iso'])
            final_df.sort_values(by=['symbol_searched', 'created_utc_iso'], ascending=[True, True], inplace=True)
            
            min_date_overall = final_df['created_utc_iso'].min()
            max_date_overall = final_df['created_utc_iso'].max()
            logger.info(f"Overall date range of collected posts: {min_date_overall.strftime('%Y-%m-%d')} to {max_date_overall.strftime('%Y-%m-%d')}")

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
                        f"Target limit per ticker/sub: {SEARCH_LIMIT_PER_SUBREDDIT_PER_TICKER}\n\n"
                        f"Total posts collected: {total_posts_collected_overall}\n"
                        f"Date range in data: {min_date_overall.strftime('%Y-%m-%d')} to {max_date_overall.strftime('%Y-%m-%d')}\n"
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
            except Exception as e_save:
                logger.error(f"Error saving Reddit data to CSV or sending email: {e_save}", exc_info=True)
        else:
            logger.info("Final DataFrame for Reddit data is empty. No CSV created.")
    else:
        logger.info("No posts collected at all. No CSV created.")
        
    logger.info(f"--- Reddit Historical Data Collection Script Finished ---")
