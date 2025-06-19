# reddit_historical_pilot.py
import praw
import os
import pandas as pd
from datetime import datetime, timezone
import logging
import time 

# --- הגדרות פיילוט ---
TEST_SYMBOL_FOR_REDDIT = "GME"        # סמל לבדיקה
TEST_SUBREDDIT = "wallstreetbets"     # סאברדיט לבדיקה
SEARCH_LIMIT_PER_SUB = 30             # מגבלה נמוכה לבדיקה ראשונית של time_filter='all'
SEARCH_TIME_FILTER = "all"            # <<<--- השינוי כאן!
OUTPUT_CSV_FILENAME = f"reddit_historical_pilot_{TEST_SYMBOL_FOR_REDDIT}_{TEST_SUBREDDIT}_{SEARCH_TIME_FILTER}_limit{SEARCH_LIMIT_PER_SUB}.csv"

# --- ניסיון לייבא פונקציות עזר ---
EMAIL_SENDER_AVAILABLE = False
try:
    from email_sender import send_email 
    from settings import setup_logger 
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("RedditHistoricalPilot", level=logging.DEBUG) 
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("RedditHistoricalPilot_Fallback")
    logger.warning("Could not import from email_sender or settings. Email functionality will be disabled. Using basic logger.")

# -- קריאת פרטי API של Reddit ממשתני סביבה --
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SentibotPilot/0.2 by YourRedditUsername") 

reddit_client_instance = None 
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    logger.critical("Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET) are not set in environment variables. Reddit scraper will not function.")
else:
    if not REDDIT_USER_AGENT or "YourRedditUsername" in REDDIT_USER_AGENT or "your_username" in REDDIT_USER_AGENT.lower():
        logger.warning(f"Reddit User-Agent may be generic ('{REDDIT_USER_AGENT}'). Consider setting a unique REDDIT_USER_AGENT (e.g., 'SentibotPilot/0.2 by MyRedditBotUsername').")
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

def fetch_historical_reddit_posts(symbol: str, 
                                 subreddit_name: str, 
                                 limit: int, 
                                 time_filter: str,
                                 min_body_len: int = 10) -> list[dict]:
    if reddit_client_instance is None:
        logger.error("Reddit client (PRAW) is not initialized. Cannot fetch posts.")
        return []

    collected_posts = []
    search_query = f'"{symbol}"' 
    
    logger.info(f"Fetching Reddit posts for query: '{search_query}' in r/{subreddit_name} (Sort: top, Limit: {limit}, Time Filter: {time_filter})")

    try:
        subreddit = reddit_client_instance.subreddit(subreddit_name)
        submissions = subreddit.search(query=search_query, sort='top', time_filter=time_filter, limit=limit)
        
        processed_count = 0
        for submission in submissions:
            processed_count += 1
            if submission.stickied or submission.over_18:
                logger.debug(f"  Skipping stickied/over_18 post ID {submission.id}")
                continue

            post_title = submission.title.strip()
            post_body = submission.selftext.strip() if submission.selftext else ""
            
            if not post_title and (not post_body or len(post_body) < min_body_len) :
                logger.debug(f"  Skipping post ID {submission.id} due to empty title and short/empty body.")
                continue

            post_url = submission.url
            post_id = submission.id
            post_created_utc = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            post_created_iso = post_created_utc.isoformat()

            collected_posts.append({
                "symbol_searched": symbol,
                "subreddit": subreddit_name,
                "post_id": post_id,
                "title": post_title,
                "body": post_body, 
                "url": post_url,
                "created_utc_iso": post_created_iso,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "flair": str(submission.link_flair_text) 
            })
            logger.debug(f"  Collected post ({len(collected_posts)}): '{post_title[:80]}...' (Date: {post_created_iso}, Score: {submission.score})")
        
        logger.info(f"Processed {processed_count} submissions from PRAW. Collected {len(collected_posts)} valid posts from r/{subreddit_name} for query '{search_query}'.")

    except praw.exceptions.PRAWException as praw_error:
         logger.error(f"A PRAW-specific error occurred while fetching from r/{subreddit_name} for '{symbol}': {praw_error}")
    except Exception as general_error:
        logger.error(f"An unexpected error occurred while fetching from r/{subreddit_name} for '{symbol}': {general_error}", exc_info=True)
    
    return collected_posts

if __name__ == "__main__":
    logger.info(f"--- Starting Reddit Historical Scraper Pilot for symbol: {TEST_SYMBOL_FOR_REDDIT} in r/{TEST_SUBREDDIT} ---")
    logger.info(f"Parameters: Limit={SEARCH_LIMIT_PER_SUB}, Time Filter='{SEARCH_TIME_FILTER}'")
    
    if reddit_client_instance: 
        posts = fetch_historical_reddit_posts(
            symbol=TEST_SYMBOL_FOR_REDDIT,
            subreddit_name=TEST_SUBREDDIT,
            limit=SEARCH_LIMIT_PER_SUB,
            time_filter=SEARCH_TIME_FILTER
        )
        
        if posts:
            logger.info(f"Successfully scraped {len(posts)} posts.")
            df = pd.DataFrame(posts)
            
            if not df.empty:
                df['created_utc_iso'] = pd.to_datetime(df['created_utc_iso'])
                df.sort_values(by='created_utc_iso', ascending=True, inplace=True) # מיין מהישן לחדש
                
                logger.info("\n--- Scraped Reddit Posts DataFrame (Oldest First - Sample of 5) ---")
                print_df = df[['created_utc_iso', 'title', 'score', 'num_comments', 'flair']].copy()
                print_df['title'] = print_df['title'].str.slice(0, 70) + '...' 
                logger.info(f"\n{print_df.head().to_string()}")
                
                # בדוק את טווח התאריכים שקיבלנו
                if not df.empty:
                    min_date = df['created_utc_iso'].min()
                    max_date = df['created_utc_iso'].max()
                    logger.info(f"Date range of collected posts: {min_date} to {max_date}")

                try:
                    df.to_csv(OUTPUT_CSV_FILENAME, index=False, encoding='utf-8-sig')
                    logger.info(f"Scraped Reddit data saved to {OUTPUT_CSV_FILENAME}")

                    if EMAIL_SENDER_AVAILABLE and os.path.exists(OUTPUT_CSV_FILENAME):
                        email_subject = f"Sentibot - Reddit Historical Pilot Results ({TEST_SYMBOL_FOR_REDDIT} in r/{TEST_SUBREDDIT})"
                        email_body = (
                            f"Reddit historical scraper pilot finished for symbol {TEST_SYMBOL_FOR_REDDIT} in r/{TEST_SUBREDDIT}.\n"
                            f"Time filter: {SEARCH_TIME_FILTER}, Search limit: {SEARCH_LIMIT_PER_SUB}.\n"
                            f"Scraped {len(posts)} posts.\n"
                            f"Date range in data: {min_date.strftime('%Y-%m-%d') if not df.empty else 'N/A'} to {max_date.strftime('%Y-%m-%d') if not df.empty else 'N/A'}\n\n"
                            f"The data is attached as '{OUTPUT_CSV_FILENAME}'.\n\n"
                            f"Sentibot"
                        )
                        
                        email_sent = send_email(
                            subject=email_subject,
                            body=email_body,
                            attachment_paths=[OUTPUT_CSV_FILENAME] 
                        )

                        if email_sent:
                            logger.info(f"Email with Reddit pilot results CSV sent successfully.")
                        else:
                            logger.error(f"Failed to send email with Reddit pilot results CSV.")
                    elif not EMAIL_SENDER_AVAILABLE:
                        logger.warning("Email sending is not available.")
                    elif not os.path.exists(OUTPUT_CSV_FILENAME):
                        logger.warning(f"Output file {OUTPUT_CSV_FILENAME} not found for email attachment.")
                except Exception as e_save_email:
                    logger.error(f"Error saving CSV or sending email: {e_save_email}")
            else:
                logger.info("DataFrame of posts is empty after processing.")
        else:
            logger.info(f"No posts were scraped for {TEST_SYMBOL_FOR_REDDIT} in r/{TEST_SUBREDDIT} with the given parameters.")
    else:
        logger.error("Cannot run pilot because Reddit client (PRAW) was not initialized. Check API credentials and User-Agent.")
        
    logger.info(f"--- Reddit Historical Scraper Pilot Finished ---")
