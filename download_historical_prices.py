import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time # לשליטה על קצב הבקשות
import os # נוסף עבור בדיקת קיום קובץ ושליפת שם קובץ

# נניח ש-email_sender.py ו-settings.py נמצאים באותו project root
# או שהם ניתנים לייבוא בסביבת ההרצה.
# אם יש בעיית ייבוא, ייתכן שנצטרך להתאים את נתיבי הייבוא או להעתיק קוד.
try:
    from email_sender import send_email # מייבאים את הפונקציה הגנרית
    from settings import setup_logger # מייבאים את הלוגר אם רוצים להשתמש בו גם כאן
    EMAIL_SENDER_AVAILABLE = True
    main_logger = setup_logger("PriceDownloader") # לוגר ייעודי לסקריפט הזה
except ImportError:
    EMAIL_SENDER_AVAILABLE = False
    # לוגר בסיסי אם settings לא זמין
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main_logger = logging.getLogger("PriceDownloader_Fallback")
    main_logger.warning("Could not import from email_sender or settings. Email functionality will be disabled.")

# רשימת הסמלים מהמסמך
TICKERS = [
    "TSLA", "META", "NVDA", "AMD", "GME", "AMC", "PLTR", "COIN", "BB", "CVNA", 
    "SPCE", "NKLA", "LCID", "NIO", "XPEV", "RIVN", "MULN", "SOFI", "MARA", 
    "RIOT", "MSTR", "AI", "BBAI", "SOUN", "TLRY", "NVAX", "SAVA", "ENVX", 
    "EOSE", "DWAC", "FFIE", "ACHR", "CHPT", "SMCI", "UPST", "DKNG", "BYND", 
    "DNA", "SNDL", "FSR"
]

# הגדרת טווח התאריכים
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365) 

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

all_stocks_data = pd.DataFrame()
output_filename = "historical_prices_sentiment_universe.csv" # שם קובץ הפלט

main_logger.info(f"Starting download of historical data for {len(TICKERS)} tickers...")
main_logger.info(f"Date range: {start_date_str} to {end_date_str}")

for i, ticker_symbol in enumerate(TICKERS):
    main_logger.info(f"\nProcessing ticker {i+1}/{len(TICKERS)}: {ticker_symbol}")
    try:
        ticker_data = yf.download(ticker_symbol, 
                                  start=start_date_str, 
                                  end=end_date_str,
                                  progress=False, 
                                  show_errors=True)

        if ticker_data.empty:
            main_logger.warning(f"  No data found for {ticker_symbol} in the given date range.")
            continue

        ticker_data['Ticker'] = ticker_symbol
        ticker_data.reset_index(inplace=True)
        
        if all_stocks_data.empty:
            all_stocks_data = ticker_data
        else:
            all_stocks_data = pd.concat([all_stocks_data, ticker_data], ignore_index=True)
        
        main_logger.info(f"  Successfully downloaded {len(ticker_data)} data points for {ticker_symbol}.")

    except Exception as e:
        main_logger.error(f"  An error occurred while downloading data for {ticker_symbol}: {e}")
    
    time.sleep(0.5) 

if not all_stocks_data.empty:
    desired_columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    existing_desired_columns = [col for col in desired_columns if col in all_stocks_data.columns]
    all_stocks_data = all_stocks_data[existing_desired_columns]

    try:
        all_stocks_data.to_csv(output_filename, index=False, encoding='utf-8-sig')
        main_logger.info(f"\nHistorical data for all tickers saved to: {output_filename}")
        main_logger.info(f"Total rows in combined CSV: {len(all_stocks_data)}")

        # --- שליחת הקובץ במייל ---
        if EMAIL_SENDER_AVAILABLE:
            # המשתנים EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER צריכים להיות מוגדרים כמשתני סביבה
            # או ש- send_email יקרא אותם מ-settings.py אם הוא מיובא משם.
            # פונקציית send_email שלך כבר מטפלת בבדיקת המשתנים האלה.
            
            email_subject = f"Sentibot - Historical Prices Data ({end_date_str})"
            email_body = (
                f"Historical price data collection finished for {len(TICKERS)} tickers.\n"
                f"Date range: {start_date_str} to {end_date_str}.\n\n"
                f"The data is attached as '{output_filename}'.\n\n"
                f"Total rows: {len(all_stocks_data)}\n\n"
                f"Sentibot"
            )
            
            # כאן נשתמש בפונקציה send_email הגנרית שלך
            # היא צריכה לקבל attachment_paths כרשימה
            email_sent = send_email(
                subject=email_subject,
                body=email_body,
                # receiver_email יילקח מ-os.getenv("EMAIL_RECEIVER") בתוך send_email
                attachment_paths=[output_filename] # שלח את הקובץ שיצרנו
            )

            if email_sent:
                main_logger.info(f"Email with historical prices CSV sent successfully.")
            else:
                main_logger.error(f"Failed to send email with historical prices CSV. Check email configurations and logs from email_sender.")
        else:
            main_logger.warning("Email sending is not available (could not import email_sender or settings). Please retrieve the file manually.")
        # --- סוף שליחת המייל ---

    except Exception as e_save:
        main_logger.error(f"Error saving data to CSV: {e_save}")
else:
    main_logger.warning("\nNo data was downloaded for any ticker. Output file not created, and no email sent.")

main_logger.info("Script finished.")
