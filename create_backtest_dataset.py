import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay 
import numpy as np 
import requests 

# --- הגדרות ---
EMAIL_SENDER_AVAILABLE = False
SENTIMENT_ANALYZER_AVAILABLE = False
try:
    from email_sender import send_email
    from settings import setup_logger
    EMAIL_SENDER_AVAILABLE = True
    logger = setup_logger("CreateBacktestDataset", level=logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("CreateBacktestDataset_Fallback")
    logger.warning("Could not import from email_sender or settings. Email/advanced logging functionality may be limited.")

try:
    from sentiment_analyzer import analyze_sentiment 
    SENTIMENT_ANALYZER_AVAILABLE = True
    logger.info("Sentiment analyzer imported successfully.")
except ImportError:
    logger.error("Could not import 'analyze_sentiment' from sentiment_analyzer.py. Sentiment analysis will assign default scores.")
    def analyze_sentiment(text, source_name=None): return 0.0 

# --- קישורים לקבצים ב-Google Drive (מעודכנים לפי מה ששלחת) ---
# קובץ מחירי המניות ההיסטוריים
PRICES_FILE_ID = "1D6mQpdzjWB3vmAaHgKFwTcIobtw4-vrf" # <--- ה-ID של historical_prices_sentiment_universe (2)
PRICES_GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?export=download&id={PRICES_FILE_ID}"
LOCAL_PRICES_CSV_PATH = "downloaded_historical_prices.csv"

# קובץ הרדיט המעובד
REDDIT_FILE_ID = "1U-PAdgwwTpShr9DiiEisOA1T-ht3_YWg" # <--- ה-ID של reddit_processed_daily_text_20250619
REDDIT_GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?export=download&id={REDDIT_FILE_ID}"
LOCAL_REDDIT_PROCESSED_CSV_PATH = "downloaded_reddit_processed_daily.csv"

# --- שם קובץ הפלט הסופי ---
FINAL_BACKTEST_DATASET_CSV = f"backtesting_dataset_v1_{datetime.now().strftime('%Y%m%d')}.csv"

# --- פרמטרים לחישוב תשואות עתידיות ---
FUTURE_RETURN_DAYS = [1, 2, 3, 5, 10] 

def download_file_from_google_drive(file_id: str, destination: str, file_description: str):
    logger.info(f"Attempting to download {file_description} from Google Drive (ID: {file_id}) to {destination}...")
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, stream=True, timeout=120) 
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=81920): 
                f.write(chunk)
        download_size_mb = os.path.getsize(destination)/(1024*1024) if os.path.exists(destination) else 0
        logger.info(f"{file_description} downloaded successfully to {destination} ({download_size_mb:.2f} MB).")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {file_description}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during download of {file_description}: {e}")
        return False

def load_and_prepare_reddit_data(filepath: str) -> pd.DataFrame:
    logger.info(f"Loading processed Reddit data from: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Reddit data file not found: {filepath}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        required_cols = ['Date', 'Ticker', 'combined_reddit_text_for_day', 'num_relevant_posts_today', 'avg_score_today', 'avg_num_comments_today']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in Reddit data: {missing_cols}. Cannot proceed.")
            return pd.DataFrame()
            
        df.dropna(subset=['Date', 'Ticker', 'combined_reddit_text_for_day'], inplace=True)
        logger.info(f"Loaded {len(df)} valid rows from processed Reddit data.")
        return df
    except Exception as e:
        logger.error(f"Error loading processed Reddit data from {filepath}: {e}", exc_info=True)
        return pd.DataFrame()

def load_and_prepare_price_data(filepath: str) -> pd.DataFrame:
    logger.info(f"Loading historical price data from: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Price data file not found: {filepath}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        required_cols = ['Date', 'Ticker', 'Open', 'Close', 'High', 'Low', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in Price data: {missing_cols}. Cannot proceed.")
            return pd.DataFrame()

        df.dropna(subset=required_cols, inplace=True)
        logger.info(f"Loaded {len(df)} valid rows from historical price data.")
        return df
    except Exception as e:
        logger.error(f"Error loading historical price data from {filepath}: {e}", exc_info=True)
        return pd.DataFrame()

def calculate_sentiment_scores(df_reddit: pd.DataFrame) -> pd.DataFrame:
    if not SENTIMENT_ANALYZER_AVAILABLE:
        logger.warning("Sentiment analyzer not available. Assigning default sentiment score 0.0.")
        df_reddit['avg_daily_reddit_sentiment'] = 0.0
        return df_reddit
    
    if 'combined_reddit_text_for_day' not in df_reddit.columns:
        logger.error("'combined_reddit_text_for_day' column missing. Cannot calculate sentiment.")
        df_reddit['avg_daily_reddit_sentiment'] = 0.0
        return df_reddit

    logger.info(f"Calculating sentiment scores for {len(df_reddit)} Reddit daily texts...")
    df_reddit['avg_daily_reddit_sentiment'] = df_reddit['combined_reddit_text_for_day'].apply(
        lambda text: analyze_sentiment(text=str(text), source_name="Reddit_Combined")
    )
    logger.info("Finished calculating sentiment scores.")
    return df_reddit

def calculate_future_returns(df_merged_with_prices: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating future returns...")
    # ודא שהעמודה 'Date' היא מסוג datetime לפני המיון
    df_merged_with_prices['Date'] = pd.to_datetime(df_merged_with_prices['Date'])
    df_calc = df_merged_with_prices.sort_values(by=['Ticker', 'Date']).copy()

    for days in FUTURE_RETURN_DAYS:
        logger.info(f"  Calculating for T+{days} business days...")
        
        # פתיחה של יום המסחר הבא (T+1 Open) - ישמש כנקודת כניסה
        df_calc[f'Entry_Open_T+1B'] = df_calc.groupby('Ticker')['Open'].shift(-1) # BDay(1)
        
        # מחיר הסגירה N ימי עסקים *אחרי יום הכניסה* (T+1+N)
        # ה-shift צריך להיות שלילי כדי להסתכל קדימה
        # shift(-(days)) ייתן את הנתון מ-N ימי עסקים קדימה מהשורה הנוכחית (T+N).
        # אנחנו רוצים את הנתון מ-N ימי עסקים אחרי יום הכניסה (T+1), כלומר (N+1) מהיום הנוכחי T.
        df_calc[f'Future_Close_{days}B_after_Entry'] = df_calc.groupby('Ticker')['Close'].shift(-(days + 1))
        df_calc[f'Future_High_{days}B_after_Entry'] = df_calc.groupby('Ticker')['High'].shift(-(days + 1))
        df_calc[f'Future_Low_{days}B_after_Entry'] = df_calc.groupby('Ticker')['Low'].shift(-(days + 1))

        entry_price_col = f'Entry_Open_T+1B'
        exit_price_col = f'Future_Close_{days}B_after_Entry'
        return_col = f'Return_{days}B_vs_T+1Open_Pct'
        
        valid_prices = df_calc[entry_price_col].notna() & df_calc[exit_price_col].notna() & (df_calc[entry_price_col] != 0)
        
        df_calc.loc[valid_prices, return_col] = \
            ((df_calc.loc[valid_prices, exit_price_col] - df_calc.loc[valid_prices, entry_price_col]) / df_calc.loc[valid_prices, entry_price_col]) * 100
        
        df_calc[return_col] = df_calc[return_col].round(2)

    logger.info("Finished calculating future returns.")
    return df_calc

if __name__ == "__main__":
    logger.info(f"--- Starting Script: Create Backtest Dataset ---")

    prices_downloaded = download_file_from_google_drive(PRICES_FILE_ID, LOCAL_PRICES_CSV_PATH, "Historical Prices CSV")
    reddit_data_downloaded = download_file_from_google_drive(REDDIT_FILE_ID, LOCAL_REDDIT_PROCESSED_CSV_PATH, "Processed Reddit Data CSV")

    if not (prices_downloaded and reddit_data_downloaded):
        logger.critical("Failed to download one or both necessary data files. Aborting.")
        exit()

    df_reddit_processed = load_and_prepare_reddit_data(LOCAL_REDDIT_PROCESSED_CSV_PATH)
    df_prices_historical = load_and_prepare_price_data(LOCAL_PRICES_CSV_PATH)

    if df_reddit_processed.empty or df_prices_historical.empty:
        logger.error("One or both input dataframes are empty after loading. Aborting.")
        exit()

    df_reddit_with_sentiment = calculate_sentiment_scores(df_reddit_processed)
    
    df_reddit_to_merge = df_reddit_with_sentiment[[
        'Date', 'Ticker', 'avg_daily_reddit_sentiment', 
        'num_relevant_posts_today', 'avg_score_today', 
        'avg_num_comments_today', 'combined_reddit_text_for_day'
    ]].copy()

    logger.info("Merging Reddit sentiment data with price data...")
    df_prices_historical['Date'] = pd.to_datetime(df_prices_historical['Date'])
    df_reddit_to_merge['Date'] = pd.to_datetime(df_reddit_to_merge['Date'])
    
    # שימוש ב-merge 'inner' כדי לשמור רק ימים שיש להם נתונים משני המקורות
    df_merged = pd.merge(df_prices_historical, df_reddit_to_merge, on=['Date', 'Ticker'], how='inner')
    
    if df_merged.empty:
        logger.error("DataFrame is empty after merging price and sentiment data. Check date ranges and ticker consistency. Aborting.")
        exit()
        
    logger.info(f"Merged DataFrame shape: {df_merged.shape}. Contains data for days with both price and Reddit sentiment info.")
    logger.info(f"Number of unique Tickers in merged data: {df_merged['Ticker'].nunique()}")
    logger.info(f"Date range in merged data: {df_merged['Date'].min().strftime('%Y-%m-%d')} to {df_merged['Date'].max().strftime('%Y-%m-%d')}")

    df_final = calculate_future_returns(df_merged) 

    if not df_final.empty:
        try:
            # בחר את העמודות הסופיות שברצונך לשמור, בסדר הרצוי
            final_columns_to_keep = [
                'Date', 'Ticker', 
                'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close', # מחירים מקוריים של יום T
                'avg_daily_reddit_sentiment', 'num_relevant_posts_today', 
                'avg_score_today', 'avg_num_comments_today', 'combined_reddit_text_for_day' # נתוני רדיט
            ]
            # הוסף את עמודות התשואה העתידית שנוצרו
            for days in FUTURE_RETURN_DAYS:
                final_columns_to_keep.append(f'Entry_Open_T+1B')
                final_columns_to_keep.append(f'Future_Close_{days}B_after_Entry')
                final_columns_to_keep.append(f'Future_High_{days}B_after_Entry')
                final_columns_to_keep.append(f'Future_Low_{days}B_after_Entry')
                final_columns_to_keep.append(f'Return_{days}B_vs_T+1Open_Pct')
            
            # השאר רק את העמודות האלה, וודא שהן קיימות
            existing_final_columns = [col for col in final_columns_to_keep if col in df_final.columns]
            df_to_save = df_final[existing_final_columns]

            df_to_save.to_csv(FINAL_BACKTEST_DATASET_CSV, index=False, encoding='utf-8-sig', date_format='%Y-%m-%dT%H:%M:%S.%f')
            logger.info(f"Final backtesting dataset saved to: {FINAL_BACKTEST_DATASET_CSV}")
            logger.info(f"Final DataFrame shape: {df_to_save.shape}")
            logger.debug(f"Sample of final DataFrame head:\n{df_to_save.head().to_string()}")

            if EMAIL_SENDER_AVAILABLE and os.path.exists(FINAL_BACKTEST_DATASET_CSV):
                email_subject = f"Sentibot - Final Backtesting Dataset Ready ({datetime.now().strftime('%Y-%m-%d')})"
                email_body = (
                    f"The final dataset for backtesting has been generated.\n\n"
                    f"Source Reddit data file (after download): {LOCAL_REDDIT_PROCESSED_CSV_PATH}\n"
                    f"Source Price data file (after download): {LOCAL_PRICES_CSV_PATH}\n"
                    f"Output file: {FINAL_BACKTEST_DATASET_CSV}\n\n"
                    f"Total rows in final dataset: {len(df_to_save)}\n"
                    f"Unique tickers in final dataset: {df_to_save['Ticker'].nunique()}\n"
                    f"Date range in final dataset: {df_to_save['Date'].min().strftime('%Y-%m-%d')} to {df_to_save['Date'].max().strftime('%Y-%m-%d')}\n\n"
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
            
            if os.path.exists(LOCAL_PRICES_CSV_PATH):
                logger.info(f"Deleting temporary downloaded prices file: {LOCAL_PRICES_CSV_PATH}")
                os.remove(LOCAL_PRICES_CSV_PATH)
            if os.path.exists(LOCAL_REDDIT_PROCESSED_CSV_PATH):
                logger.info(f"Deleting temporary downloaded Reddit data file: {LOCAL_REDDIT_PROCESSED_CSV_PATH}")
                os.remove(LOCAL_REDDIT_PROCESSED_CSV_PATH)

        except Exception as e_save_final:
            logger.error(f"Error saving final dataset or sending email: {e_save_final}", exc_info=True)
    else:
        logger.warning("Final dataset is empty after all processing. No output file created.")

    logger.info(f"--- Create Backtest Dataset Script Finished ---")
