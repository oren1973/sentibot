# reddit_scraper.py
import praw
import os
from settings import setup_logger, MIN_HEADLINE_LENGTH 

logger = setup_logger(__name__)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Sentibot/0.3 by YourRedditUsername") 

DEFAULT_SUBREDDITS = ["stocks", "wallstreetbets", "StockMarket", "investing", "SecurityAnalysis"]
SUBREDDITS_TO_SCRAPE = DEFAULT_SUBREDDITS

try:
    LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "15"))
    COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "3"))
except ValueError:
    logger.warning("Could not parse Reddit limit/comments parameters from environment variables. Using defaults.")
    LIMIT_PER_SUBREDDIT = 15
    COMMENTS_PER_POST = 3

reddit_client_instance = None 
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
        )
        logger.info("PRAW client initialized (read-only status: {}).".format(reddit_client_instance.read_only))
    except Exception as e:
        logger.critical(f"Failed to initialize PRAW Reddit client: {e}", exc_info=True)
        reddit_client_instance = None

def get_reddit_posts(symbol: str, 
                     subreddits_list: list[str] = None, 
                     limit_per_sub: int = None, 
                     comments_limit: int = None
                     ) -> list[tuple[str, str]]:
    if reddit_client_instance is None:
        logger.error("Reddit client (PRAW) is not initialized. Cannot fetch posts.")
        return []

    subreddits_to_use = subreddits_list if subreddits_list is not None else SUBREDDITS_TO_SCRAPE
    actual_limit_per_sub = limit_per_sub if limit_per_sub is not None else LIMIT_PER_SUBREDDIT
    actual_comments_limit = comments_limit if comments_limit is not None else COMMENTS_PER_POST
    
    source_type_post = "Reddit_Post"
    source_type_comment = "Reddit_Comment"
    collected_texts_with_source = []
    
    search_query = f'"{symbol}"'

    logger.info(f"Fetching Reddit content for '{symbol}' from subreddits: {subreddits_to_use} (Query: {search_query}, Limit/sub: {actual_limit_per_sub}, Comments/post: {actual_comments_limit})")

    for sub_name in subreddits_to_use:
        logger.debug(f"Searching r/{sub_name} for query: '{search_query}'...")
        try:
            subreddit_instance = reddit_client_instance.subreddit(sub_name)
            submissions = subreddit_instance.search(query=search_query, sort='top', time_filter='week', limit=actual_limit_per_sub)
            
            processed_posts_in_sub = 0
            for submission in submissions:
                if submission.stickied or submission.over_18:
                    continue

                post_title = submission.title.strip()
                post_body = ""
                if submission.selftext:
                    post_body = submission.selftext.strip()
                
                full_post_content = post_title
                if post_body:
                    full_post_content = f"{post_title}. {post_body}"

                if full_post_content and len(full_post_content) >= MIN_HEADLINE_LENGTH:
                    collected_texts_with_source.append((full_post_content, source_type_post))
                    processed_posts_in_sub += 1

                    try:
                        submission.comments.replace_more(limit=0) 
                        valid_comments = []
                        for c in submission.comments:
                            if hasattr(c, 'body') and c.body and hasattr(c, 'score'):
                                valid_comments.append(c)
                        
                        top_comments = sorted(valid_comments, key=lambda c: c.score, reverse=True)[:actual_comments_limit]

                        for comment in top_comments:
                            comment_body_text = comment.body.strip()
                            if comment_body_text and len(comment_body_text) >= MIN_HEADLINE_LENGTH:
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
