import pandas as pd
import requests
import os
import logging
import re # עבור ניקוי טקסט עם ביטויים רגולריים
import json # אם נרצה לשמור משהו מורכב יותר, כרגע פחות קריטי כאן
from datetime import datetime 

# --- הגדרות ---
try:
    from email_sender import send_email
    from settings import setup_logger, MIN_HEADLINE_LENGTH # נייבא MIN_HEADLINE_LENGTH לסינון גוף הפוסט
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("ProcessRedditData", level=logging.INFO)
except ImportError:
    EMAIL_SENDER_AVAILABLE = False
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("ProcessRedditData_Fallback")
    logger.warning("Could not import from email_sender or settings. Email/advanced logging functionality may be limited.")
    MIN_HEADLINE_LENGTH = 10 # ברירת מחדל אם לא מיובא

# הקישור הישיר לקובץ ה-CSV שלך ב-Google Drive
GOOGLE_DRIVE_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id=1wxqWXzURwINQB9HZ-OyocvB6wJRvgEso"
DOWNLOADED_RAW_CSV_PATH = "downloaded_reddit_historical_raw.csv" # שם הקובץ כפי שיישמר זמנית בענן
PROCESSED_DAILY_CSV_PATH = f"reddit_processed_daily_text_{datetime.now().strftime('%Y%m%d')}.csv"

# --- פרמטרים לסינון ועיבוד ---
# פליירים שנרצה לשמור (אחרים יסוננו החוצה). None יישמר (פוסטים ללא פלייר)
# המר את הרשימה ל-set של אותיות קטנות לבדיקה מהירה ולא תלוית רישיות
VALID_FLAIRS_TO_KEEP_LOWER = {
    None, 'none', 'dd', 'news', 'discussion', 'catalyst', 
    'technical analysis', 'yolo', 'gain', 'loss', 'earnings thread', 'advice'
}

MIN_POST_SCORE_FOR_BODY_ONLY_RELEVANCE = 20 # אם הסמל רק בגוף, דרוש ניקוד כזה
MIN_BODY_LENGTH_FOR_BODY_ONLY_RELEVANCE = 50 # ואורך גוף כזה

def download_file_from_google_drive(url, destination):
    logger.info(f"Attempting to download file from Google Drive URL to {destination}...")
    try:
        response = requests.get(url, stream=True, timeout=60) # timeout מוגדל ל-60 שניות
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        logger.info(f"File downloaded successfully to {destination}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during download: {e}")
        return False

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower() # אותיות קטנות
    text = re.sub(r'http\S+|www.\S+', '', text) # הסר URLs
    text = re.sub(r'\n+', ' ', text) # החלף שורות חדשות ברווח
    text = re.sub(r'[^a-z0-9\s.,\'"$!?]', '', text) # השאר רק אותיות, מספרים, וסימני פיסוק נפוצים
    text = re.sub(r'\s+', ' ', text).strip() # הסר רווחים כפולים
    return text

if __name__ == "__main__":
    logger.info("--- Starting Reddit Data Processing Script ---")

    if not download_file_from_google_drive(GOOGLE_DRIVE_DOWNLOAD_URL, DOWNLOADED_RAW_CSV_PATH):
        logger.error("Failed to download Reddit data file. Aborting.")
        exit()

    if not os.path.exists(DOWNLOADED_RAW_CSV_PATH):
        logger.error(f"Downloaded file {DOWNLOADED_RAW_CSV_PATH} not found after download attempt. Aborting.")
        exit()
    
    logger.info(f"Loading raw Reddit data from {DOWNLOADED_RAW_CSV_PATH}...")
    try:
        df_raw = pd.read_csv(DOWNLOADED_RAW_CSV_PATH)
        logger.info(f"Successfully loaded {len(df_raw)} raw Reddit posts.")
    except Exception as e:
        logger.error(f"Failed to load raw Reddit CSV: {e}", exc_info=True)
        exit()

    # 1. טיפול ראשוני בנתונים
    df = df_raw.copy()
    df['created_utc_iso'] = pd.to_datetime(df['created_utc_iso'], errors='coerce')
    df.dropna(subset=['created_utc_iso'], inplace=True) # הסר שורות ללא תאריך תקין
    df['date_only'] = df['created_utc_iso'].dt.date # עמודת תאריך בלבד

    df['title'] = df['title'].fillna('').astype(str)
    df['body'] = df['body'].fillna('').astype(str)
    df['flair'] = df['flair'].fillna('None').astype(str).str.lower() # נרמל פליירים לאותיות קטנות וטפל ב-NaN

    logger.info(f"Initial number of posts: {len(df)}")

    # 2. סינון לפי פלייר
    df = df[df['flair'].isin(VALID_FLAIRS_TO_KEEP_LOWER)]
    logger.info(f"Posts after flair filtering: {len(df)}")

    # 3. סינון לפי רלוונטיות לסמל
    df['symbol_in_title'] = df.apply(lambda row: str(row['symbol_searched']).lower() in row['title'].lower(), axis=1)
    df['symbol_in_body'] = df.apply(lambda row: str(row['symbol_searched']).lower() in row['body'].lower(), axis=1)
    
    condition_title = df['symbol_in_title']
    condition_body_strong = (
        df['symbol_in_body'] & 
        (df['score'] >= MIN_POST_SCORE_FOR_BODY_ONLY_RELEVANCE) & 
        (df['body'].str.len() >= MIN_BODY_LENGTH_FOR_BODY_ONLY_RELEVANCE)
    )
    
    df_relevant = df[condition_title | condition_body_strong].copy() # OR לוגי
    logger.info(f"Posts after symbol relevance filtering: {len(df_relevant)}")

    if df_relevant.empty:
        logger.warning("No relevant posts found after filtering. Exiting.")
        exit()

    # 4. ניקוי טקסט (על הכותרת והגוף בנפרד)
    logger.info("Cleaning text for titles and bodies...")
    df_relevant['title_cleaned'] = df_relevant['title'].apply(clean_text)
    df_relevant['body_cleaned'] = df_relevant['body'].apply(clean_text)

    # 5. יצירת טקסט מאוחד לניתוח סנטימנט
    # נשאיר רק פוסטים שבהם יש טקסט כלשהו אחרי ניקוי
    df_relevant['text_for_sentiment'] = df_relevant.apply(
        lambda row: (row['title_cleaned'] + ". " + row['body_cleaned']).strip('. '), 
        axis=1
    )
    df_relevant = df_relevant[df_relevant['text_for_sentiment'].str.len() >= MIN_HEADLINE_LENGTH].copy()
    logger.info(f"Posts after ensuring text_for_sentiment is not too short: {len(df_relevant)}")
    
    if df_relevant.empty:
        logger.warning("No posts with sufficient text for sentiment analysis after cleaning. Exiting.")
        exit()

    # 6. צבירה יומית לכל מניה
    logger.info("Aggregating relevant Reddit text per symbol per day...")
    daily_aggregated_text = df_relevant.groupby(['date_only', 'symbol_searched']).agg(
        combined_reddit_text_for_day=('text_for_sentiment', lambda x: ' \n '.join(x)), # חבר טקסטים עם שורה חדשה
        num_relevant_posts_today=('post_id', 'count'),
        avg_score_today = ('score', 'mean'),
        avg_num_comments_today = ('num_comments', 'mean')
    ).reset_index()

    daily_aggregated_text.rename(columns={'date_only': 'Date', 'symbol_searched': 'Ticker'}, inplace=True)
    daily_aggregated_text['Date'] = pd.to_datetime(daily_aggregated_text['Date']) # המר חזרה ל-datetime מלא
    logger.info(f"Generated {len(daily_aggregated_text)} daily aggregated records for Reddit sentiment input.")
    logger.debug(f"Sample of daily aggregated data:\n{daily_aggregated_text.head().to_string()}")

    # 7. שמירת ה-DataFrame המעובד
    if not daily_aggregated_text.empty:
        try:
            daily_aggregated_text.to_csv(PROCESSED_DAILY_CSV_PATH, index=False, encoding='utf-8-sig', date_format='%Y-%m-%d')
            logger.info(f"Processed Reddit data saved to: {PROCESSED_DAILY_CSV_PATH}")

            if EMAIL_SENDER_AVAILABLE and os.path.exists(PROCESSED_DAILY_CSV_PATH):
                email_subject = f"Sentibot - Processed Daily Reddit Data ({datetime.now().strftime('%Y-%m-%d')})"
                email_body = (
                    f"Reddit historical data has been processed.\n"
                    f"Input raw posts: {len(df_raw)}\n"
                    f"Posts after flair filtering: {len(df[df['flair'].isin(VALID_FLAIRS_TO_KEEP_LOWER)])}\n" # חישוב מחדש לצורך הדוח
                    f"Posts after symbol relevance filtering: {len(df_relevant[condition_title | condition_body_strong])}\n"
                    f"Posts with sufficient text for sentiment: {len(df_relevant)}\n"
                    f"Total daily aggregated records: {len(daily_aggregated_text)}\n\n"
                    f"The processed data is attached as '{PROCESSED_DAILY_CSV_PATH}'.\n\n"
                    f"Sentibot"
                )
                
                email_sent = send_email(
                    subject=email_subject,
                    body=email_body,
                    attachment_paths=[PROCESSED_DAILY_CSV_PATH]
                )
                if email_sent:
                    logger.info(f"Email with processed Reddit data CSV sent successfully.")
                else:
                    logger.error(f"Failed to send email with processed Reddit data CSV.")
            
            # נקה את הקובץ הגולמי שהורדנו אם רוצים לחסוך מקום
            if os.path.exists(DOWNLOADED_RAW_CSV_PATH):
                logger.info(f"Deleting temporary raw downloaded file: {DOWNLOADED_RAW_CSV_PATH}")
                os.remove(DOWNLOADED_RAW_CSV_PATH)

        except Exception as e_save_proc:
            logger.error(f"Error saving processed Reddit data or sending email: {e_save_proc}", exc_info=True)
    else:
        logger.warning("No data to save after processing and aggregation.")

    logger.info("--- Reddit Data Processing Script Finished ---")
