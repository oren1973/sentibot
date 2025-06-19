import pandas as pd
import numpy as np
import os
import logging
import requests 
from datetime import datetime 

# --- הגדרות ---
EMAIL_SENDER_AVAILABLE = False
ANALYSIS_LOG_FILENAME = f"analysis_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt" # שם קובץ הלוג של הניתוח

try:
    from email_sender import send_email
    from settings import setup_logger, REPORTS_OUTPUT_DIR # נייבא את REPORTS_OUTPUT_DIR
    EMAIL_SENDER_AVAILABLE = True
    
    # הגדרת הלוגר הראשי שיכתוב גם לקונסול וגם לקובץ
    logger = setup_logger("AnalyzeBacktestData", level=logging.INFO)
    
    # ודא שהתיקייה קיימת
    if not os.path.exists(REPORTS_OUTPUT_DIR):
        os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
        
    analysis_log_filepath = os.path.join(REPORTS_OUTPUT_DIR, ANALYSIS_LOG_FILENAME)
    
    # הוספת FileHandler ללוגר הראשי
    file_handler = logging.FileHandler(analysis_log_filepath, mode='w', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # פורמט פשוט יותר לקובץ
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.info(f"Analysis output will also be saved to: {analysis_log_filepath}")

except ImportError:
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(ANALYSIS_LOG_FILENAME, mode='w', encoding='utf-8')])
    logger = logging.getLogger("AnalyzeBacktestData_Fallback")
    logger.warning("Could not import from email_sender or settings. Email functionality may be limited. Using basic file logger.")
    analysis_log_filepath = ANALYSIS_LOG_FILENAME # שמור בתיקייה הנוכחית

try:
    from sentiment_analyzer import analyze_sentiment 
    SENTIMENT_ANALYZER_AVAILABLE = True # נשאר מהקוד הקודם, למרות שלא בשימוש כאן
except ImportError:
    logger.error("Could not import 'analyze_sentiment'. This script doesn't use it directly but indicates a potential issue.")


# --- קישורים לקבצים ב-Google Drive (מעודכנים לפי מה ששלחת) ---
BACKTEST_DATASET_FILE_ID = "1p8uIjfpOD2As9A_i08Q2fHUSkXwi2_D0" 
BACKTEST_DATASET_GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?export=download&id={BACKTEST_DATASET_FILE_ID}"
LOCAL_BACKTEST_CSV_PATH = "downloaded_backtesting_dataset.csv" 

FUTURE_RETURN_DAYS = [1, 2, 3, 5, 10] 

def download_file_from_google_drive(file_id: str, destination: str, file_description: str):
    # ... (הפונקציה נשארת זהה לקודם) ...
    logger.info(f"Attempting to download {file_description} from Google Drive (ID: {file_id}) to {destination}...")
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, stream=True, timeout=180) 
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
    # הודעת הפתיחה הזו תיכתב גם לקובץ הלוג של הניתוח
    logger.info(f"--- Starting Analysis of Backtest Dataset ---")

    if not download_file_from_google_drive(BACKTEST_DATASET_FILE_ID, LOCAL_BACKTEST_CSV_PATH, "Final Backtest Dataset"):
        logger.error("Failed to download the backtest dataset. Aborting analysis.")
        return

    if not os.path.exists(LOCAL_BACKTEST_CSV_PATH):
        logger.error(f"Dataset file {LOCAL_BACKTEST_CSV_PATH} not found after download attempt. Aborting analysis.")
        return

    try:
        df_backtest = pd.read_csv(LOCAL_BACKTEST_CSV_PATH)
        df_backtest['Date'] = pd.to_datetime(df_backtest['Date'], errors='coerce') 
        df_backtest.dropna(subset=['Date'], inplace=True)
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
    for days in FUTURE_RETURN_DAYS: # השתמש ב-FUTURE_RETURN_DAYS שהוגדר למעלה
        col = f'Return_{days}B_vs_T+1Open_Pct' 
        if col in df_backtest.columns:
            cols_for_corr.append(col)
            return_cols_to_check.append(col)
        else:
            logger.warning(f"Return column {col} not found in dataset.")
    
    if 'avg_daily_reddit_sentiment' in df_backtest.columns and len(return_cols_to_check) > 0:
        df_corr = df_backtest[cols_for_corr].dropna()
        if not df_corr.empty and len(df_corr) > 1: 
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

        for days_horizon in FUTURE_RETURN_DAYS: # השתמש ב-FUTURE_RETURN_DAYS
            return_col = f'Return_{days_horizon}B_vs_T+1Open_Pct'
            if return_col in df_backtest.columns:
                logger.info(f"\n--- Analysis for {days_horizon}-Day Future Return by Sentiment Group ---")
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
        df_high_posts = df_backtest[df_backtest['num_relevant_posts_today'] > 5].copy() 
        
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
    for ticker_to_analyze in ["TSLA", "GME", "AAPL", "NVDA", "AMC"]: # הרחבתי קצת את הרשימה
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
    
    # --- שליחת קובץ הלוג של הניתוח במייל ---
    logger.info(f"\n--- Analysis Script Finished. Preparing to email analysis log: {analysis_log_filepath} ---")
    if EMAIL_SENDER_AVAILABLE and os.path.exists(analysis_log_filepath):
        email_subject = f"Sentibot - Backtest Dataset Analysis Results ({datetime.now().strftime('%Y-%m-%d')})"
        email_body = (
            f"The analysis of the backtesting dataset is complete.\n"
            f"The full analysis output log is attached.\n\n"
            f"Input dataset (downloaded to): {LOCAL_BACKTEST_CSV_PATH}\n"
            f"Number of rows in input dataset: {len(df_backtest) if 'df_backtest' in locals() else 'N/A'}\n\n"
            f"Sentibot"
        )
        email_sent = send_email(
            subject=email_subject,
            body=email_body,
            attachment_paths=[analysis_log_filepath] # שלח את קובץ הלוג של הניתוח
        )
        if email_sent:
            logger.info(f"Email with analysis log sent successfully.")
        else:
            logger.error(f"Failed to send email with analysis log.")
    elif not os.path.exists(analysis_log_filepath):
        logger.error(f"Analysis log file {analysis_log_filepath} not found for email attachment.")
    
    # נקה את הקובץ שהורדנו מ-Google Drive
    if os.path.exists(LOCAL_BACKTEST_CSV_PATH):
        logger.info(f"Deleting temporary downloaded dataset file: {LOCAL_BACKTEST_CSV_PATH}")
        try:
            os.remove(LOCAL_BACKTEST_CSV_PATH)
        except Exception as e_del:
            logger.warning(f"Could not delete temporary file {LOCAL_BACKTEST_CSV_PATH}: {e_del}")

if __name__ == "__main__":
    run_analysis()
