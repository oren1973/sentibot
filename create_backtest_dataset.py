import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay # לחישוב ימי עסקים
import numpy as np # עבור חישובים מספריים

# --- נסיונות ייבוא ---
EMAIL_SENDER_AVAILABLE = False
SENTIMENT_ANALYZER_AVAILABLE = False
try:
    from email_sender import send_email
    from settings import setup_logger, MIN_HEADLINE_LENGTH # MIN_HEADLINE_LENGTH לא בשימוש ישיר כאן
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("CreateBacktestDataset", level=logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("CreateBacktestDataset_Fallback")
    logger.warning("Could not import from email_sender or settings. Email/advanced logging functionality may be limited.")

try:
    from sentiment_analyzer import analyze_sentiment # הפונקציה שלך מ-VADER
    SENTIMENT_ANALYZER_AVAILABLE = True
    logger.info("Sentiment analyzer imported successfully.")
except ImportError:
    logger.error("Could not import 'analyze_sentiment' from sentiment_analyzer.py. Sentiment analysis will not be performed.")
    # פונקציית דמה אם המקורית לא זמינה, כדי שהסקריפט לא ייכשל לגמרי
    def analyze_sentiment(text, source_name=None): return 0.0 

# --- שמות קבצי קלט ופלט ---
# !!! שנה את שם הקובץ של הרדיט לשם המדויק שלך !!!
REDDIT_PROCESSED_DATA_CSV = "reddit_processed_daily_text_20250619.csv" # <--- שנה לשם הקובץ שלך!
HISTORICAL_PRICES_CSV = "historical_prices_sentiment_universe.csv"
FINAL_BACKTEST_DATASET_CSV = f"backtesting_dataset_v1_{datetime.now().strftime('%Y%m%d')}.csv"

# --- פרמטרים לחישוב תשואות עתידיות ---
# נחשב תשואה אם קונים בפתיחה של היום שאחרי ההחלטה (t+1) ומוכרים בסגירה של t+N
# N ימי עסקים קדימה לחישוב תשואות
FUTURE_RETURN_DAYS = [1, 2, 3, 5, 10] 

def load_and_prepare_reddit_data(filepath: str) -> pd.DataFrame:
    logger.info(f"Loading processed Reddit data from: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Reddit data file not found: {filepath}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date', 'Ticker', 'combined_reddit_text_for_day'], inplace=True)
        logger.info(f"Loaded {len(df)} rows from processed Reddit data.")
        return df
    except Exception as e:
        logger.error(f"Error loading processed Reddit data: {e}", exc_info=True)
        return pd.DataFrame()

def load_and_prepare_price_data(filepath: str) -> pd.DataFrame:
    logger.info(f"Loading historical price data from: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Price data file not found: {filepath}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # ודא שהעמודות הנדרשות קיימות
        required_cols = ['Date', 'Ticker', 'Open', 'Close', 'High', 'Low', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Required column '{col}' missing in price data. Aborting.")
                return pd.DataFrame()
        df.dropna(subset=required_cols, inplace=True)
        logger.info(f"Loaded {len(df)} rows from historical price data.")
        return df
    except Exception as e:
        logger.error(f"Error loading historical price data: {e}", exc_info=True)
        return pd.DataFrame()

def calculate_sentiment_scores(df_reddit: pd.DataFrame) -> pd.DataFrame:
    if not SENTIMENT_ANALYZER_AVAILABLE:
        logger.warning("Sentiment analyzer not available. Skipping sentiment score calculation.")
        df_reddit['avg_daily_reddit_sentiment'] = 0.0 # ערך דמה
        return df_reddit
    
    logger.info(f"Calculating sentiment scores for {len(df_reddit)} Reddit daily texts...")
    sentiments = []
    for index, row in df_reddit.iterrows():
        if (index + 1) % 100 == 0: # הדפס התקדמות כל 100 שורות
            logger.info(f"  Processed {index+1}/{len(df_reddit)} sentiment calculations...")
        # כאן אנחנו מנתחים את הטקסט המאוחד.
        # פונקציית analyze_sentiment שלך יכולה לקבל source_name.
        # מכיוון שהטקסט הוא כבר מאוחד מרדיט, אפשר להעביר "Reddit_Combined" או לא להעביר כלל,
        # תלוי אם יש לך משקלים ספציפיים לזה ב-NEWS_SOURCES_CONFIG.
        # אם אין, VADER יפעל כרגיל.
        sentiment = analyze_sentiment(text=row['combined_reddit_text_for_day'], source_name="Reddit_Combined")
        sentiments.append(sentiment)
    
    df_reddit['avg_daily_reddit_sentiment'] = sentiments
    logger.info("Finished calculating sentiment scores.")
    return df_reddit

def calculate_future_returns(df_merged: pd.DataFrame, price_df_full: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating future returns...")
    df_result = df_merged.copy()

    for days_ahead in FUTURE_RETURN_DAYS:
        logger.info(f"  Calculating for T+{days_ahead} days...")
        # עמודות חדשות לכל טווח זמן
        future_open_col = f'Future_Open_{days_ahead}D'
        future_close_col = f'Future_Close_{days_ahead}D'
        future_high_col = f'Future_High_{days_ahead}D'
        future_low_col = f'Future_Low_{days_ahead}D'
        return_vs_next_open_col = f'Return_vs_NextOpen_{days_ahead}D_Pct' # תשואה מקנייה בפתיחה של T+1 למכירה בסגירה של T+N
        
        df_result[future_open_col] = pd.NA
        df_result[future_close_col] = pd.NA
        df_result[future_high_col] = pd.NA
        df_result[future_low_col] = pd.NA
        df_result[return_vs_next_open_col] = pd.NA

        # כדי למצוא מחירים עתידיים, נשתמש ב-shift על נתוני המחירים המקוריים הממוינים
        # ודא ש-price_df_full ממוין לפי טיקר ואז תאריך
        price_df_full_sorted = price_df_full.sort_values(by=['Ticker', 'Date'])

        # מחיר הפתיחה של יום המסחר הבא (T+1 Open)
        # נשתמש ב-groupby().shift(-1) כדי לקבל את הערך של השורה הבאה *בתוך כל קבוצת טיקר*
        next_day_open_map = price_df_full_sorted.groupby('Ticker')['Open'].shift(-1)
        
        # מחירי סגירה, גבוה, נמוך עתידיים (T+N Close/High/Low)
        # shift(-(days_ahead)) יקבל את הערך N שורות קדימה (בתוך כל קבוצת טיקר)
        future_close_map = price_df_full_sorted.groupby('Ticker')['Close'].shift(-(days_ahead))
        future_high_map = price_df_full_sorted.groupby('Ticker')['High'].shift(-(days_ahead))
        future_low_map = price_df_full_sorted.groupby('Ticker')['Low'].shift(-(days_ahead))

        # מיפוי הערכים ל-df_result
        # ניישר את האינדקסים כדי שהמיפוי יעבוד על סמך האינדקס המקורי של price_df_full_sorted
        # זה קצת מורכב בגלל ש-df_result הוא תת-קבוצה (אחרי מיזוג עם נתוני סנטימנט)
        # דרך פשוטה יותר היא למזג את המחירים העתידיים חזרה
        
        # יצירת עמודות תאריך עתידי למיזוג
        df_result_temp = df_result[['Ticker', 'Date']].copy()
        # התאריך לקנייה הוא יום העסקים הבא
        df_result_temp[f'Trade_Entry_Date_{days_ahead}D'] = df_result_temp['Date'] + BDay(1)
        # התאריך למכירה/בדיקה הוא N ימי עסקים אחרי תאריך הקנייה
        df_result_temp[f'Future_Target_Date_{days_ahead}D'] = df_result_temp[f'Trade_Entry_Date_{days_ahead}D'] + BDay(days_ahead -1) # BDay(0) זה אותו יום
        
        # מזג עם מחירי הפתיחה של יום הכניסה
        price_df_full_sorted['Date'] = pd.to_datetime(price_df_full_sorted['Date']) # ודא פורמט
        
        # מחיר כניסה (Open למחרת)
        df_result_temp = pd.merge(
            df_result_temp,
            price_df_full_sorted[['Ticker', 'Date', 'Open']],
            left_on=['Ticker', f'Trade_Entry_Date_{days_ahead}D'],
            right_on=['Ticker', 'Date'],
            how='left',
            suffixes=('', '_entry')
        )
        df_result_temp.rename(columns={'Open': future_open_col, 'Date_entry':f'Actual_Entry_Date_{days_ahead}D'}, inplace=True)
        df_result_temp.drop(columns=['Date_entry'], inplace=True, errors='ignore')


        # מחיר יעד (Close, High, Low ביום היעד)
        df_result_temp = pd.merge(
            df_result_temp,
            price_df_full_sorted[['Ticker', 'Date', 'Close', 'High', 'Low']],
            left_on=['Ticker', f'Future_Target_Date_{days_ahead}D'],
            right_on=['Ticker', 'Date'],
            how='left',
            suffixes=('', '_target')
        )
        df_result_temp.rename(columns={
            'Close': future_close_col, 
            'High': future_high_col,
            'Low': future_low_col,
            'Date_target': f'Actual_Target_Date_{days_ahead}D'}, inplace=True)
        df_result_temp.drop(columns=['Date_target'], inplace=True, errors='ignore')
        
        # העתק את התוצאות חזרה ל-df_result המקורי
        # נשתמש באינדקס המקורי של df_result כדי להבטיח שהשורות מתאימות
        df_result = pd.merge(df_result, 
                             df_result_temp[['Ticker', 'Date', future_open_col, future_close_col, future_high_col, future_low_col]],
                             on=['Ticker', 'Date'],
                             how='left')

        # חישוב התשואה
        # ודא שהעמודות הן מספריות ושאין ערכי NaN לפני החישוב
        valid_prices = df_result[future_open_col].notna() & df_result[future_close_col].notna()
        df_result.loc[valid_prices, return_vs_next_open_col] = \
            ((df_result.loc[valid_prices, future_close_col] - df_result.loc[valid_prices, future_open_col]) / df_result.loc[valid_prices, future_open_col]) * 100
        
        # עיגול התשואה
        df_result[return_vs_next_open_col] = df_result[return_vs_next_open_col].round(2)

    logger.info("Finished calculating future returns.")
    return df_result

if __name__ == "__main__":
    logger.info(f"--- Starting Script: Create Backtest Dataset ---")

    # 1. טעינת נתונים
    df_reddit = load_and_prepare_reddit_data(REDDIT_PROCESSED_DATA_CSV)
    df_prices = load_and_prepare_price_data(HISTORICAL_PRICES_CSV)

    if df_reddit.empty or df_prices.empty:
        logger.error("One or both input dataframes are empty. Aborting.")
        exit()

    # 2. חישוב סנטימנט על נתוני Reddit
    df_reddit_with_sentiment = calculate_sentiment_scores(df_reddit)
    # שמור את עמודות המפתח למיזוג
    df_reddit_to_merge = df_reddit_with_sentiment[['Date', 'Ticker', 'avg_daily_reddit_sentiment', 'num_relevant_posts_today', 'avg_score_today', 'avg_num_comments_today', 'combined_reddit_text_for_day']].copy()

    # 3. מיזוג נתוני סנטימנט עם נתוני מחירים
    logger.info("Merging Reddit sentiment data with price data...")
    # ודא שפורמט התאריכים תואם לפני המיזוג
    df_prices['Date'] = pd.to_datetime(df_prices['Date'])
    df_reddit_to_merge['Date'] = pd.to_datetime(df_reddit_to_merge['Date'])
    
    df_merged = pd.merge(df_prices, df_reddit_to_merge, on=['Date', 'Ticker'], how='left')
    # המיזוג 'left' ישאיר את כל רשומות המחירים, ויוסיף NaN לסנטימנט אם אין נתוני רדיט לאותו יום/מניה
    # אפשר לשקול 'inner' אם רוצים רק ימים שיש להם גם מחיר וגם סנטימנט
    logger.info(f"Merged DataFrame shape: {df_merged.shape}. Contains data for days with price info.")
    logger.info(f"Number of rows with Reddit sentiment after merge: {df_merged['avg_daily_reddit_sentiment'].notna().sum()}")

    # 4. חישוב תשואות עתידיות
    # df_prices המקורי משמש כאן כמקור לכלל המחירים ההיסטוריים לחישוב ה-shift
    df_final = calculate_future_returns(df_merged, df_prices) 

    # 5. שמירת ה-Dataset הסופי
    if not df_final.empty:
        try:
            df_final.to_csv(FINAL_BACKTEST_DATASET_CSV, index=False, encoding='utf-8-sig', date_format='%Y-%m-%dT%H:%M:%S.%f') # שמירה בפורמט ISO מלא
            logger.info(f"Final backtesting dataset saved to: {FINAL_BACKTEST_DATASET_CSV}")
            logger.info(f"Final DataFrame shape: {df_final.shape}")
            logger.debug(f"Sample of final DataFrame head:\n{df_final.head().to_string()}")

            if EMAIL_SENDER_AVAILABLE and os.path.exists(FINAL_BACKTEST_DATASET_CSV):
                email_subject = f"Sentibot - Final Backtesting Dataset Ready ({datetime.now().strftime('%Y-%m-%d')})"
                email_body = (
                    f"The final dataset for backtesting has been generated.\n\n"
                    f"Source Reddit data file: {REDDIT_PROCESSED_DATA_CSV}\n"
                    f"Source Price data file: {HISTORICAL_PRICES_CSV}\n"
                    f"Output file: {FINAL_BACKTEST_DATASET_CSV}\n\n"
                    f"Total rows in final dataset: {len(df_final)}\n"
                    f"Unique tickers in final dataset: {df_final['Ticker'].nunique()}\n"
                    f"Date range in final dataset: {df_final['Date'].min().strftime('%Y-%m-%d')} to {df_final['Date'].max().strftime('%Y-%m-%d')}\n\n"
                    f"Sentibot"
                )
                email_sent = send_email(
                    subject=email_subject,
                    body=email_body,
                    attachment_paths=[FINAL_BACKTEST_DATASET_CSV]
                )
                if email_sent:
                    logger.info(f"Email with final backtesting dataset CSV sent successfully.")
                else:
                    logger.error(f"Failed to send email with final backtesting dataset CSV.")
        except Exception as e_save_final:
            logger.error(f"Error saving final dataset or sending email: {e_save_final}", exc_info=True)
    else:
        logger.warning("Final dataset is empty. No output file created.")

    logger.info(f"--- Create Backtest Dataset Script Finished ---")
