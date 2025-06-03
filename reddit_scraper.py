# reddit_scraper.py
import praw
import os
# from datetime import datetime, timedelta # לא בשימוש כרגע במודול זה
from settings import setup_logger

logger = setup_logger(__name__)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# עדכן את שם המשתמש שלך!
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "sentibot/0.2 by YourRedditUsername") 

# בדיקה אם המפתחות קיימים
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    logger.critical("Reddit API credentials (CLIENT_ID, CLIENT_SECRET) are not set. Reddit scraper will not function.")
    # אפשר להעלות חריגה כאן אם רוצים שהאפליקציה תיכשל אם אין מפתחות
    # raise ValueError("Reddit API credentials not found.")
    reddit = None # הגדרת reddit כ-None כדי שהפונקציה תיכשל בצורה נקייה
else:
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            # הוספת timeout לבקשות של PRAW (מומלץ)
            # request_timeout=10 # לדוגמה, 10 שניות. בדוק את התיעוד של PRAW לפרמטר המדויק
        )
        # בדיקה שהחיבור תקין (קריאה קלה שלא עולה הרבה)
        reddit.user.me() # יחזיר None אם האותנטיקציה היא read-only (app-only) וזה בסדר
        logger.info("Successfully initialized Reddit API client.")
    except Exception as e:
        logger.critical(f"Failed to initialize Reddit API client: {e}", exc_info=True)
        reddit = None


def get_reddit_posts(symbol: str, 
                     subreddits: list[str] = None, 
                     limit_per_subreddit: int = 15, 
                     comments_per_post: int = 3
                     ) -> list[tuple[str, str]]: # (text, source_type)
    """
    שולף פוסטים ותגובות מ-Reddit עבור סמל נתון.
    מחזיר רשימה של tuples: (טקסט, סוג מקור כמו "Reddit_Post" או "Reddit_Comment").
    """
    if reddit is None:
        logger.error("Reddit client not initialized. Cannot fetch posts.")
        return []

    if subreddits is None:
        subreddits = ["stocks", "wallstreetbets", "StockMarket", "investing"] # ברירת מחדל טובה יותר

    source_type_post = "Reddit_Post"
    source_type_comment = "Reddit_Comment"
    collected_texts = []
    
    logger.info(f"Fetching Reddit posts for {symbol} from subreddits: {subreddits}...")

    for sub_name in subreddits:
        try:
            logger.debug(f"Searching r/{sub_name} for '{symbol}'...")
            subreddit_instance = reddit.subreddit(sub_name)
            # שימוש ב-search עם time_filter='week' יכול להיות מוגבל. 
            # אפשר לשקול 'month' או חיפוש ב-hot/new אם רוצים מידע עדכני יותר שלא בהכרח "top"
            submissions = subreddit_instance.search(query=symbol, sort='top', time_filter='week', limit=limit_per_subreddit)
            
            post_count_for_sub = 0
            for submission in submissions:
                if submission.stickied or submission.over_18:
                    continue

                # כותרת + גוף הפוסט (אם קיים)
                post_content = submission.title
                if submission.selftext:
                    post_content = f"{submission.title}. {submission.selftext.strip()}"
                
                if post_content and len(post_content) >= 15:
                    collected_texts.append((post_content, source_type_post))
                    post_count_for_sub +=1

                    # תגובות מובילות
                    try:
                        submission.comments.replace_more(limit=0) # הסר אובייקטי "MoreComments"
                        # מיון לפי score, אם קיים
                        top_comments = sorted(
                            [c for c in submission.comments if hasattr(c, 'score') and hasattr(c, 'body') and c.body], 
                            key=lambda c: c.score, 
                            reverse=True
                        )[:comments_per_post]

                        for comment in top_comments:
                            comment_body = comment.body.strip()
                            if comment_body and len(comment_body) >= 10:
                                collected_texts.append((comment_body, source_type_comment))
                    except Exception as comment_e:
                        logger.warning(f"Error processing comments for post ID {submission.id} in r/{sub_name}: {comment_e}")
            
            logger.info(f"Found {post_count_for_sub} relevant posts in r/{sub_name} for {symbol}.")

        except praw.exceptions.PRAWException as praw_e: # שגיאות ספציפיות של PRAW
             logger.error(f"PRAW error while fetching from r/{sub_name} for {symbol}: {praw_e}")
        except Exception as e: # שאר השגיאות
            logger.error(f"Unexpected error while fetching from r/{sub_name} for {symbol}: {e}", exc_info=True)
    
    logger.info(f"Total Reddit texts collected for {symbol}: {len(collected_texts)}")
    return collected_texts
