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
    "SPCE", "NKLA", "LCID", "NIO", "XPEV", "RIVN", "MULN", "SOFI", "MARA", 
    "RIOT", "MSTR", "AI", "BBAI", "SOUN", "TLRY", "NVAX", "SAVA", "ENVX", 
    "EOSE", "DWAC", "FFIE", "ACHR", "CHPT", "SMCI", "UPST", "DKNG", "BYND", 
    "DNA", "SNDL", "FSR"
]

# סמלים שגרמו לשגיאות קודם, נסיר אותם זמנית מהרשימה הראשית
# או נטפל בהם בנפרד אם רוצים לנסות שוב
problematic_tickers = ["NKLA", "DWAC", "FFIE", "FSR"]
TICKERS_TO_DOWNLOAD = [t for t in TICKERS if t not in problematic_tickers]

end_date = datetime.now()
start_date = end_date - timedelta(days=3*365 + 1) # נוסיף יום כדי להבטיח 3 שנים מלאות גם אם "היום" עוד לא נגמר

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

output_filename = "historical_prices_sentiment_universe.csv"

main_logger.info(f"Starting download of historical data for {len(TICKERS_TO_DOWNLOAD)} tickers...")
main_logger.info(f"Date range: {start_date_str} to {end_date_str}")

all_stocks_data_df = pd.DataFrame()

try:
    # הורד נתונים עבור כל הטיקרים בבת אחת
    # yfinance יחזיר DataFrame עם MultiIndex בעמודות: (PriceType, Ticker)
    # למשל ('Open', 'TSLA'), ('Close', 'TSLA'), ('Open', 'META') וכו'.
    # האינדקס יהיה התאריכים.
    data = yf.download(
        tickers=TICKERS_TO_DOWNLOAD,
        start=start_date_str,
        end=end_date_str,
        group_by='ticker', # זה יארגן את הנתונים לפי טיקר, אבל עדיין יכול להיות מורכב
        progress=True, # אפשר להפעיל כדי לראות התקדמות אם רוצים
        threads=True # השתמש במספר threads להורדה מהירה יותר
    )

    if data.empty:
        main_logger.warning("yf.download returned an empty DataFrame. No data retrieved.")
    else:
        main_logger.info(f"Successfully downloaded data block of shape: {data.shape}")
        
        # כעת צריך "לשטח" את ה-DataFrame מהפורמט של yfinance (עם MultiIndex בעמודות)
        # לפורמט הרצוי: Ticker, Date, Open, High, Low, Close, Adj Close, Volume
        
        # אם group_by='ticker', אז data.stack(level=0) ואז unstack(level=0) יכול לעזור
        # או פשוט יותר:
        # נהפוך את ה-MultiIndex בעמודות ל-DataFrame ארוך (long format) ואז נסדר
        
        # תחילה, נבחר רק את העמודות שאנחנו צריכים (Open, High, Low, Close, Adj Close, Volume)
        # השמות שלהן יהיו ב-level 0 של ה-MultiIndex בעמודות
        columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        # נסנן את ה-DataFrame כך שיכיל רק את העמודות האלה עבור כל הטיקרים
        # זה יכול להיות מסובך אם יש טיקרים שנכשלו ולא החזירו את כל העמודות
        
        # גישה פשוטה יותר: נעבור על כל טיקר ונחלץ את הנתונים שלו
        processed_data_list = []
        for ticker in TICKERS_TO_DOWNLOAD:
            try:
                # נסה לגשת לנתונים של הטיקר הספציפי
                # אם group_by='ticker', הגישה היא data[ticker]
                # אם לא, ה-DataFrame יכול להיות עם עמודות כמו ('Open', 'AAPL'), ('Close', 'AAPL')
                if ticker in data.columns.levels[0]: # אם group_by='ticker' שימש
                    ticker_df = data[ticker].copy()
                elif (columns_to_keep[0], ticker) in data.columns: # אם הפורמט הוא (PriceType, Ticker)
                     ticker_df = data.xs(ticker, level=1, axis=1)[columns_to_keep].copy()
                else: # גישה אחרת אם הפורמט שונה (למשל, yfinance לא מקבץ לפי טיקר)
                    # נניח שהעמודות הן ('Open', ticker), ('High', ticker) וכו'.
                    # נבדוק אם לטיקר יש נתונים
                    if any((col_type, ticker) in data.columns for col_type in columns_to_keep):
                        # בחר רק את העמודות הרלוונטיות לטיקר זה
                        ticker_specific_cols = [(col_type, t) for col_type in columns_to_keep for t in [ticker] if (col_type,t) in data.columns]
                        if not ticker_specific_cols:
                            main_logger.warning(f"No data columns found for {ticker} in the downloaded block.")
                            continue
                        
                        ticker_df = data[ticker_specific_cols]
                        # שנה שמות עמודות מ-MultiIndex ל-SingleIndex
                        ticker_df.columns = [col[0] for col in ticker_df.columns]
                    else: # נסה לגשת כאילו הנתונים של טיקר בודד הם ה-DataFrame כולו
                        if ticker in data.columns.get_level_values(0): # אם יש MultiIndex והטיקר הוא ברמה הראשונה
                           ticker_df = data[ticker]
                        elif isinstance(data.columns, pd.MultiIndex) and ticker in data.columns.get_level_values(1): # אם הטיקר ברמה השנייה
                            ticker_df = data.xs(ticker, level=1, axis=1).copy()
                            ticker_df = ticker_df[columns_to_keep]
                        else: # אם אין MultiIndex והטיקרים מעורבבים (פחות סביר ל-yf.download של רשימה)
                            main_logger.warning(f"Could not reliably extract data for {ticker} from the downloaded block structure.")
                            continue


                if not ticker_df.empty:
                    ticker_df = ticker_df[columns_to_keep] # ודא שיש רק את העמודות הרצויות
                    ticker_df['Ticker'] = ticker
                    ticker_df.reset_index(inplace=True) # הפוך את 'Date' לעמודה
                    processed_data_list.append(ticker_df)
                    main_logger.info(f"  Processed data for {ticker} ({len(ticker_df)} rows).")
                else:
                    main_logger.warning(f"  No data extracted for {ticker} after attempting to structure.")
            except KeyError:
                main_logger.warning(f"  Ticker {ticker} not found in the downloaded data columns. Skipping.")
            except Exception as e_proc:
                main_logger.error(f"  Error processing data for {ticker}: {e_proc}")
        
        if processed_data_list:
            all_stocks_data_df = pd.concat(processed_data_list, ignore_index=True)
            main_logger.info(f"Successfully processed and combined data for {len(all_stocks_data_df['Ticker'].unique())} tickers.")
        else:
            main_logger.warning("No data was successfully processed from the downloaded block.")


except Exception as e:
    main_logger.error(f"An critical error occurred during yf.download or initial data processing: {e}", exc_info=True)


if not all_stocks_data_df.empty:
    desired_columns_order = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    # ודא שכל העמודות הרצויות קיימות לפני סידור מחדש, והוסף עמודות חסרות עם NaN אם צריך
    for col in desired_columns_order:
        if col not in all_stocks_data_df.columns:
            all_stocks_data_df[col] = pd.NA 
            main_logger.warning(f"Column '{col}' was missing, added with NAs.")
            
    all_stocks_data_df = all_stocks_data_df[desired_columns_order]

    try:
        all_stocks_data_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        main_logger.info(f"\nHistorical data for all tickers saved to: {output_filename}")
        main_logger.info(f"Total rows in combined CSV: {len(all_stocks_data_df)}")

        if EMAIL_SENDER_AVAILABLE:
            email_subject = f"Sentibot - Historical Prices Data ({end_date_str})"
            email_body = (
                f"Historical price data collection finished for {len(TICKERS_TO_DOWNLOAD)} tickers.\n"
                f"Date range: {start_date_str} to {end_date_str}.\n\n"
                f"The data is attached as '{output_filename}'.\n\n"
                f"Total rows: {len(all_stocks_data_df)}\n\n"
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
