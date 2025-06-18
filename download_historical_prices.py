import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time 
import os 

try:
    from email_sender import send_email 
    from settings import setup_logger 
    EMAIL_SENDER_AVAILABLE = True
    main_logger = setup_logger("PriceDownloader") 
except ImportError:
    EMAIL_SENDER_AVAILABLE = False
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main_logger = logging.getLogger("PriceDownloader_Fallback")
    main_logger.warning("Could not import from email_sender or settings. Email functionality will be disabled.")

TICKERS = [
    "TSLA", "META", "NVDA", "AMD", "GME", "AMC", "PLTR", "COIN", "BB", "CVNA", 
    "SPCE", "LCID", "NIO", "XPEV", "RIVN", "MULN", "SOFI", "MARA", 
    "RIOT", "MSTR", "AI", "BBAI", "SOUN", "TLRY", "NVAX", "SAVA", "ENVX", 
    "EOSE", "ACHR", "CHPT", "SMCI", "UPST", "DKNG", "BYND", 
    "DNA", "SNDL" # הסרתי את הסמלים הבעייתיים מהרשימה הראשית
]
# בעבר, הסמלים הבעייתיים היו: "NKLA", "DWAC", "FFIE", "FSR"
# אם תרצה לנסות אותם שוב, אפשר להוסיף אותם ל-TICKERS

end_date = datetime.now()
# +1 כדי לוודא שאנחנו מקבלים את היום הקודם במלואו אם מריצים באמצע היום
start_date = end_date - timedelta(days=3*365 + 1) 

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

output_filename = "historical_prices_sentiment_universe.csv"

main_logger.info(f"Starting download of historical data for {len(TICKERS)} tickers...")
main_logger.info(f"Date range: {start_date_str} to {end_date_str}")

all_stocks_data_df = pd.DataFrame()

try:
    # הורד נתונים עבור כל הטיקרים בבת אחת
    # yfinance יחזיר DataFrame עם MultiIndex בעמודות: (PriceType, Ticker)
    data = yf.download(
        tickers=TICKERS, # השתמש ברשימה המלאה (או המעודכנת)
        start=start_date_str,
        end=end_date_str,
        # group_by='ticker', # נסיר את זה, ברירת המחדל טובה יותר לעיבוד הבא
        progress=True, 
        threads=True 
    )

    if data.empty:
        main_logger.warning("yf.download returned an empty DataFrame. No data retrieved.")
    else:
        main_logger.info(f"Successfully downloaded data block of shape: {data.shape}")
        main_logger.debug(f"Sample of downloaded data columns: {data.columns[:10]}") # הצג דוגמה לעמודות

        # --- עיבוד ה-DataFrame עם MultiIndex ---
        # הרמה העליונה של העמודות היא סוג הנתון (Adj Close, Close, High, Low, Open, Volume)
        # הרמה התחתונה היא הטיקר
        
        # השתמש ב-stack() כדי להעביר את רמת הטיקרים מהעמודות לאינדקס
        data_stacked = data.stack(level=1) # מעביר את הרמה השנייה (טיקרים) לאינדקס
        
        if data_stacked.empty:
            main_logger.warning("DataFrame became empty after stacking. Check download structure.")
        else:
            # כעת האינדקס הוא (Date, Ticker) והעמודות הן (Adj Close, Close, ...)
            # אפס את האינדקס כדי שהתאריך והטיקר יהפכו לעמודות רגילות
            data_reset = data_stacked.reset_index()
            
            # שנה שמות עמודות אם צריך (בדרך כלל השמות כבר תקינים)
            # data_reset.rename(columns={'level_1': 'Ticker', 'Date': 'Date'}, inplace=True)
            # השם של עמודת הטיקר אחרי stack עשוי להיות 'Ticker' או 'Symbols' או משהו אחר, תלוי בגרסת yfinance
            # נבדוק איך לקרוא לה נכון:
            if 'Ticker' in data_reset.columns:
                pass # השם כבר 'Ticker'
            elif 'Symbols' in data_reset.columns: # שם נפוץ אחר
                data_reset.rename(columns={'Symbols': 'Ticker'}, inplace=True)
            else: # נסה למצוא את עמודת הטיקר (זו שלא 'Date' ולא סוגי מחיר)
                potential_ticker_cols = [col for col in data_reset.columns if col not in ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
                if len(potential_ticker_cols) == 1:
                    main_logger.info(f"Renaming ticker column from '{potential_ticker_cols[0]}' to 'Ticker'.")
                    data_reset.rename(columns={potential_ticker_cols[0]: 'Ticker'}, inplace=True)
                else:
                    main_logger.error(f"Could not reliably identify the ticker column after stacking. Columns found: {data_reset.columns.tolist()}")
            
            all_stocks_data_df = data_reset
            main_logger.info(f"Successfully processed and combined data. Shape of final DataFrame: {all_stocks_data_df.shape}")
            main_logger.debug(f"Sample of final DataFrame head:\n{all_stocks_data_df.head()}")

except Exception as e:
    main_logger.error(f"An critical error occurred during yf.download or data processing: {e}", exc_info=True)


if not all_stocks_data_df.empty:
    desired_columns_order = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    
    # ודא שכל העמודות הרצויות קיימות, אחרת הוסף אותן עם NA
    for col in desired_columns_order:
        if col not in all_stocks_data_df.columns:
            all_stocks_data_df[col] = pd.NA 
            main_logger.warning(f"Column '{col}' was missing in the final DataFrame, added with NAs. This might indicate issues with specific tickers during download/processing.")
            
    all_stocks_data_df = all_stocks_data_df[desired_columns_order]

    try:
        all_stocks_data_df.to_csv(output_filename, index=False, encoding='utf-8-sig', date_format='%Y-%m-%d') # הוספתי date_format
        main_logger.info(f"\nHistorical data for all tickers saved to: {output_filename}")
        main_logger.info(f"Total rows in combined CSV: {len(all_stocks_data_df)}")

        if EMAIL_SENDER_AVAILABLE:
            email_subject = f"Sentibot - Historical Prices Data ({datetime.now().strftime('%Y-%m-%d')})" # השתמש בתאריך הנוכחי
            email_body = (
                f"Historical price data collection finished.\n"
                f"Tickers attempted: {len(TICKERS)}\n"
                f"Date range: {start_date_str} to {end_date_str}.\n\n"
                f"The data is attached as '{output_filename}'.\n\n"
                f"Total rows in CSV: {len(all_stocks_data_df)}\n"
                f"Unique tickers in CSV: {all_stocks_data_df['Ticker'].nunique()}\n\n"
                f"Sentibot"
            )
            
            email_sent = send_email(
                subject=email_subject,
                body=email_body,
                attachment_paths=[output_filename] 
            )

            if email_sent:
                main_logger.info(f"Email with historical prices CSV sent successfully.")
            else:
                main_logger.error(f"Failed to send email with historical prices CSV. Check email configurations and logs from email_sender.")
        else:
            main_logger.warning("Email sending is not available. Please retrieve the file manually if run in cloud.")

    except Exception as e_save:
        main_logger.error(f"Error saving data to CSV: {e_save}")
else:
    main_logger.warning("\nNo data was downloaded or processed for any ticker. Output file not created, and no email sent.")

main_logger.info("Script finished.")
