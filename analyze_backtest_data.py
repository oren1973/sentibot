import pandas as pd
import numpy as np
import os
import logging
import requests # עבור הורדה
from datetime import datetime # עבור שם קובץ הפלט

# --- הגדרות ---
EMAIL_SENDER_AVAILABLE = False # לא נשלח מייל מהסקריפט הזה, רק מדפיסים ללוג
try:
    from settings import setup_logger
    logger = setup_logger("AnalyzeBacktestData", level=logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("AnalyzeBacktestData_Fallback")
    logger.warning("Could not import setup_logger from settings. Using basic logger.")

# --- קישור לקובץ ה-Dataset ב-Google Drive ---
BACKTEST_DATASET_FILE_ID = "1p8uIjfpOD2As9A_i08Q2fHUSkXwi2_D0" # ה-ID מהקישור שלך
BACKTEST_DATASET_GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?export=download&id={BACKTEST_DATASET_FILE_ID}"
LOCAL_BACKTEST_CSV_PATH = "downloaded_backtesting_dataset.csv" # שם הקובץ כפי שיישמר זמנית בענן

def download_file_from_google_drive(file_id: str, destination: str, file_description: str):
    logger.info(f"Attempting to download {file_description} from Google Drive (ID: {file_id}) to {destination}...")
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, stream=True, timeout=180) # Timeout ארוך יותר, 3 דקות
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

def run_analysis():
    logger.info(f"--- Starting Analysis of Backtest Dataset ---")

    if not download_file_from_google_drive(BACKTEST_DATASET_FILE_ID, LOCAL_BACKTEST_CSV_PATH, "Final Backtest Dataset"):
        logger.error("Failed to download the backtest dataset. Aborting analysis.")
        return

    if not os.path.exists(LOCAL_BACKTEST_CSV_PATH):
        logger.error(f"Dataset file {LOCAL_BACKTEST_CSV_PATH} not found after download attempt. Aborting analysis.")
        return

    try:
        df_backtest = pd.read_csv(LOCAL_BACKTEST_CSV_PATH)
        # חשוב לוודא שהמרת התאריך מתבצעת נכון, בהתאם לפורמט שבו הוא נשמר
        df_backtest['Date'] = pd.to_datetime(df_backtest['Date'], errors='coerce') 
        df_backtest.dropna(subset=['Date'], inplace=True) # הסר שורות עם תאריך לא תקין
        logger.info(f"Successfully loaded dataset with {len(df_backtest)} rows from {LOCAL_BACKTEST_CSV_PATH}.")
    except Exception as e:
        logger.error(f"Error loading dataset {LOCAL_BACKTEST_CSV_PATH}: {e}", exc_info=True)
        return

    if df_backtest.empty:
        logger.warning("Dataset is empty. No analysis to perform.")
        return

    # --- א. קורלציה כללית בין סנטימנט לתשואות ---
    logger.info("\n--- Correlation Matrix (Sentiment vs Future Returns) ---")
    cols_for_corr = ['avg_daily_reddit_sentiment']
    return_cols_to_check = []
    for days in [1, 2, 3, 5, 10]:
        col = f'Return_{days}B_vs_T+1Open_Pct' # שם העמודה כפי שהוא נוצר בסקריפט הקודם
        if col in df_backtest.columns:
            cols_for_corr.append(col)
            return_cols_to_check.append(col)
        else:
            logger.warning(f"Return column {col} not found in dataset.")
    
    if 'avg_daily_reddit_sentiment' in df_backtest.columns and len(return_cols_to_check) > 0:
        # הסר שורות עם NaN באחת מהעמודות הרלוונטיות לקורלציה
        df_corr = df_backtest[cols_for_corr].dropna()
        if not df_corr.empty and len(df_corr) > 1: # צריך לפחות 2 דגימות לקורלציה
            correlation_matrix = df_corr.corr()
            logger.info(f"\nCorrelation Matrix (based on {len(df_corr)} rows):\n{correlation_matrix.to_string()}")
        else:
            logger.warning("Not enough data points after dropping NaNs to calculate correlation matrix.")
    else:
        logger.warning("Required columns for sentiment/return correlation not found or no return columns available.")

    # --- ב. ניתוח לפי קבוצות סנטימנט ---
    logger.info("\n--- Average Future Returns by Sentiment Group ---")
    bins = [-1.1, -0.5, -0.05, 0.05, 0.5, 1.1] 
    labels = ['Very Negative (< -0.5)', 'Negative (-0.5 to -0.05)', 'Neutral (-0.05 to 0.05)', 
              'Positive (0.05 to 0.5)', 'Very Positive (> 0.5)']
    
    if 'avg_daily_reddit_sentiment' in df_backtest.columns:
        df_backtest['sentiment_group'] = pd.cut(df_backtest['avg_daily_reddit_sentiment'], bins=bins, labels=labels, right=False)

        for days_horizon in [1, 2, 3, 5, 10]:
            return_col = f'Return_{days_horizon}B_vs_T+1Open_Pct'
            if return_col in df_backtest.columns:
                logger.info(f"\n--- Analysis for {days_horizon}-Day Future Return by Sentiment Group ---")
                # הצג רק אם יש ערכים שאינם NaN בעמודת התשואה
                if df_backtest[return_col].notna().any(): 
                    summary = df_backtest.groupby('sentiment_group')[return_col].agg(['mean', 'std', 'count', 'median'])
                    logger.info(f"\n{summary.to_string()}")
                else:
                    logger.info(f"All values in {return_col} are NaN. No summary to display for this horizon.")
            else:
                logger.warning(f"Return column {return_col} not found for sentiment group analysis.")
    else:
        logger.warning("'avg_daily_reddit_sentiment' column not found. Skipping sentiment group analysis.")

    # --- ג. השפעת מספר הפוסטים (num_relevant_posts_today) ---
    if 'num_relevant_posts_today' in df_backtest.columns and 'avg_daily_reddit_sentiment' in df_backtest.columns and len(return_cols_to_check) > 0:
        logger.info("\n--- Correlation: Sentiment vs Returns (High Num Posts > 5) ---")
        df_high_posts = df_backtest[df_backtest['num_relevant_posts_today'] > 5].copy() # השתמש ב-copy למנוע SettingWithCopyWarning
        
        if not df_high_posts.empty:
            df_high_posts_corr = df_high_posts[cols_for_corr].dropna()
            if not df_high_posts_corr.empty and len(df_high_posts_corr) > 1:
                correlation_high_posts = df_high_posts_corr.corr()
                logger.info(f"\nCorrelation Matrix (High Num Posts > 5, based on {len(df_high_posts_corr)} rows):\n{correlation_high_posts.to_string()}")
            else:
                logger.info("Not enough data points with >5 posts after dropping NaNs to analyze for this correlation.")
        else:
            logger.info("No data points with more than 5 posts found.")
    else:
        logger.warning("Could not perform correlation analysis for high number of posts (missing columns or no data).")

    # --- ד. ניתוח פרטני למניות ספציפיות (דוגמה ל-TSLA ו-GME) ---
    for ticker_to_analyze in ["TSLA", "GME"]:
        logger.info(f"\n--- Correlation Matrix for {ticker_to_analyze} ---")
        if 'Ticker' in df_backtest.columns and 'avg_daily_reddit_sentiment' in df_backtest.columns and len(return_cols_to_check) > 0:
            ticker_data = df_backtest[df_backtest['Ticker'] == ticker_to_analyze].copy()
            if not ticker_data.empty:
                ticker_data_corr = ticker_data[cols_for_corr].dropna()
                if not ticker_data_corr.empty and len(ticker_data_corr) > 1:
                    correlation_ticker = ticker_data_corr.corr()
                    logger.info(f"\nCorrelation Matrix for {ticker_to_analyze} (based on {len(ticker_data_corr)} rows):\n{correlation_ticker.to_string()}")
                else:
                    logger.info(f"Not enough data points for {ticker_to_analyze} after dropping NaNs to calculate correlation.")
            else:
                logger.info(f"No data for {ticker_to_analyze} in the dataset.")
        else:
             logger.warning(f"Could not perform correlation analysis for {ticker_to_analyze} (missing columns or no data).")
    
    # נקה את הקובץ שהורדנו אם רוצים
    if os.path.exists(LOCAL_BACKTEST_CSV_PATH):
        logger.info(f"Deleting temporary downloaded dataset file: {LOCAL_BACKTEST_CSV_PATH}")
        try:
            os.remove(LOCAL_BACKTEST_CSV_PATH)
        except Exception as e_del:
            logger.warning(f"Could not delete temporary file {LOCAL_BACKTEST_CSV_PATH}: {e_del}")

    logger.info("\n--- Analysis Script Finished ---")

if __name__ == "__main__":
    run_analysis()
