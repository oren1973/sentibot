# reddit_scraper.py
import praw
import os
from settings import setup_logger, MIN_HEADLINE_LENGTH # ייבוא מהקובץ settings.py

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "reddit_scraper"

# --- קריאת הגדרות Reddit ממשתני סביבה ---
# מומלץ להשאיר את פרטי האימות הרגישים כמשתני סביבה ולא בקוד.
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# ודא שאתה מגדיר User Agent ייחודי ותיאורי. החלף את 'YourRedditUsername'.
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Sentibot/0.3 by YourRedditUsername") 

# --- פרמטרים נוספים שניתן להגדיר כמשתני סביבה או בקובץ settings.py ---
DEFAULT_SUBREDDITS = ["stocks", "wallstreetbets", "StockMarket", "investing", "SecurityAnalysis"]
# אפשר לקרוא את רשימת הסאברדיטים ממשתנה סביבה אם רוצים גמישות:
# ENV_SUBREDDITS = os.getenv("REDDIT_SUBREDDITS_LIST")
# SUBREDDITS_TO_SCRAPE = [sub.strip() for sub in ENV_SUBREDDITS.split(',')] if ENV_SUBREDDITS else DEFAULT_SUBREDDITS
SUBREDDITS_TO_SCRAPE = DEFAULT_SUBREDDITS # כרגע משתמשים בברירת המחדל

try:
    # קריאת פרמטרים נוספים ממשתני סביבה עם ערכי ברירת מחדל
    LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "15"))
    COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "3"))
except ValueError:
    logger.warning("Could not parse Reddit limit/comments parameters from environment variables. Using defaults.")
    LIMIT_PER_SUBREDDIT = 15
    COMMENTS_PER_POST = 3

# --- אתחול לקוח PRAW ---
reddit_client_instance = None # הגדרה גלובלית למודול
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    logger.critical("Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET) are not set in environment variables. Reddit scraper will not function.")
else:
    if not REDDIT_USER_AGENT or "YourRedditUsername" in REDDIT_USER_AGENT or "your_username" in REDDIT_USER_AGENT.lower():
        logger.warning(f"Reddit User-Agent is generic ('{REDDIT_USER_AGENT}'). Please set a unique and descriptive REDDIT_USER_AGENT environment variable (e.g., 'Sentibot/0.3 by MyRedditBotUsername').")

    try:
        logger.info(f"Initializing PRAW client with User-Agent: {REDDIT_USER_AGENT}")
        reddit_client_instance = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            # מומלץ להוסיף timeout לבקשות של PRAW דרך קובץ praw.ini או פרמטרים אם זמין בגרסה שלך
            # request_timeout=10 # בדוק תיעוד PRAW לגבי הדרך המומלצת להגדיר timeout
        )
        # בדיקה בסיסית שהלקוח אותחל (לא מבצע קריאת API מלאה אלא אם יש צורך)
        # אם אתה משתמש באימות "script" (app-only), reddit.user.me() יחזיר None וזה תקין.
        # אם אתה משתמש באימות משתמש, זה יחזיר את פרטי המשתמש.
        # reddit_client_instance.user.me() # יכול להעלות חריגה אם האימות נכשל לגמרי
        logger.info("PRAW client initialized (read-only status: {}).".format(reddit_client_instance.read_only))
    except Exception as e:
        logger.critical(f"Failed to initialize PRAW Reddit client: {e}", exc_info=True)
        reddit_client_instance = None # ודא שהלקוח הוא None אם האתחול נכשל


def get_reddit_posts(symbol: str, 
                     subreddits_list: list[str] = None, 
                     limit_per_sub: int = None, 
                     comments_limit: int = None
                     ) -> list[tuple[str, str]]: # מחזיר (טקסט, סוג_מקור)
    """
    שולף פוסטים ותגובות מובילות מ-Reddit עבור סמל נתון.
    סוג המקור יהיה "Reddit_Post" או "Reddit_Comment".
    """
    if reddit_client_instance is None:
        logger.error("Reddit client (PRAW) is not initialized. Cannot fetch posts.")
        return []

    # שימוש בערכי ברירת מחדל אם לא סופקו פרמטרים
    subreddits_to_use = subreddits_list if subreddits_list is not None else SUBREDDITS_TO_SCRAPE
    actual_limit_per_sub = limit_per_sub if limit_per_sub is not None else LIMIT_PER_SUBREDDIT
    actual_comments_limit = comments_limit if comments_limit is not None else COMMENTS_PER_POST
    
    source_type_post = "Reddit_Post"
    source_type_comment = "Reddit_Comment"
    collected_texts_with_source = [] # רשימה של tuples
    
    # בניית מחרוזת חיפוש. אפשר להיות יותר מתוחכמים כאן (למשל, צירוף "stock" או "$SYMBOL")
    # כרגע, פשוט מחפשים את הסימול.
    search_query = f'"{symbol}"' # חיפוש מדויק יותר של הסימול, אפשר גם symbol בלבד

    logger.info(f"Fetching Reddit content for '{symbol}' from subreddits: {subreddits_to_use} (Query: {search_query}, Limit/sub: {actual_limit_per_sub}, Comments/post: {actual_comments_limit})")

    for sub_name in subreddits_to_use:
        logger.debug(f"Searching r/{sub_name} for query: '{search_query}'...")
        try:
            subreddit_instance = reddit_client_instance.subreddit(sub_name)
            
            # אפשרויות למיון ופילטור זמן:
            # sort='relevance' (ברירת מחדל), 'hot', 'top', 'new', 'comments'
            # time_filter='all', 'day', 'hour', 'month', 'week', 'year' (רלוונטי בעיקר ל-'top')
            # כרגע, 'top' ו-'week' נראה סביר לניתוח סנטימנט.
            submissions = subreddit_instance.search(query=search_query, sort='top', time_filter='week', limit=actual_limit_per_sub)
            
            processed_posts_in_sub = 0
            for submission in submissions:
                if submission.stickied or submission.over_18: # דלג על פוסטים דביקים או NSFW
                    continue

                # כותרת הפוסט
                post_title = submission.title.strip()
                
                # גוף הפוסט (אם קיים)
                post_body = ""
                if submission.selftext:
                    post_body = submission.selftext.strip()
                
                # שילוב כותרת וגוף
                full_post_content = post_title
                if post_body:
                    full_post_content = f"{post_title}. {post_body}" # הפרדה עם נקודה

                if full_post_content and len(full_post_content) >= MIN_HEADLINE_LENGTH: # אורך מינימלי גם לפוסטים
                    collected_texts_with_source.append((full_post_content, source_type_post))
                    processed_posts_in_sub += 1

                    # שליפת תגובות מובילות (אם יש תוכן לפוסט)
                    try:
                        submission.comments.replace_more(limit=0) # הסר אובייקטי "MoreComments" ביעילות
                        
                        # סינון ומיון תגובות
                        valid_comments = []
                        for c in submission.comments:
                            # ודא שלתגובה יש גוף וניקוד לפני שמוסיפים אותה
                            if hasattr(c, 'body') and c.body and hasattr(c, 'score'):
                                valid_comments.append(c)
                        
                        # מיון לפי ניקוד (score) בסדר יורד
                        top_comments = sorted(valid_comments, key=lambda c: c.score, reverse=True)[:actual_comments_limit]

                        for comment in top_comments:
                            comment_body_text = comment.body.strip()
                            if comment_body_text and len(comment_body_text) >= MIN_HEADLINE_LENGTH: # אורך מינימלי גם לתגובות
                                collected_texts_with_source.append((comment_body_text, source_type_comment))
                                
                    except Exception as comment_fetch_error:
                        logger.warning(f"Could not fetch/process comments for post ID {submission.id} in r/{sub_name}: {comment_fetch_error}")
            
            logger.info(f"Processed {processed_posts_in_sub} posts from r/{sub_name} for '{symbol}'.")

        except praw.exceptions.PRAWException as praw_error:
             logger.error(f"A PRAW-specific error occurred while fetching from r/{sub_name} for '{symbol}': {praw_error}")
        except Exception as general_error:
            logger.error(f"An unexpected error occurred while fetching from r/{sub_name} for '{symbol}': {general_error}", exc_info=True)
    
    logger.info(f"Total Reddit texts collected for '{symbol}': {len(collected_texts_with_source)} (Posts and Comments)")
    return collected_texts_with_source


if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית של ה-scraper ---
    # ודא שמשתני הסביבה של Reddit מוגדרים (ID, SECRET, USER_AGENT)
    # ודא שקובץ settings.py קיים לצורך ייבוא setup_logger
    import logging

    test_logger = setup_logger(__name__, level=logging.DEBUG)

    if reddit_client_instance is None:
        test_logger.error("Cannot run Reddit test: PRAW client not initialized. Check credentials and User-Agent.")
    else:
        test_symbols = ["TSLA", "AAPL", "GME"] # מניות עם סבירות גבוהה לדיונים
        
        # אפשר להגדיר פרמטרים ספציפיים לבדיקה
        test_subreddits = ["wallstreetbets", "stocks"] 
        test_limit_per_sub = 5 
        test_comments_limit = 2

        for sym in test_symbols:
            test_logger.info(f"--- Testing Reddit scraper for symbol: {sym} ---")
            retrieved_content = get_reddit_posts(
                symbol=sym,
                subreddits_list=test_subreddits,
                limit_per_sub=test_limit_per_sub,
                comments_limit=test_comments_limit
            )
            if retrieved_content:
                test_logger.debug(f"Retrieved {len(retrieved_content)} pieces of content for {sym}:")
                for i, (text_content, source_type) in enumerate(retrieved_content):
                    # הדפסת רק חלק מהטקסט אם הוא ארוך מאוד
                    text_preview = (text_content[:100] + '...') if len(text_content) > 103 else text_content
                    test_logger.debug(f"  {i+1}. [{source_type}] {text_preview}")
            else:
                test_logger.debug(f"No content retrieved for {sym} from Reddit with current parameters.")
            test_logger.info(f"--- Finished Reddit test for {sym} ---")
