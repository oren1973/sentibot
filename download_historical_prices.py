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

end_date = datetime.now()
start_date = end_date - timedelta(days=3*365) 

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

all_stocks_data = pd.DataFrame()
output_filename = "historical_prices_sentiment_universe.csv"

main_logger.info(f"Starting download of historical data for {len(TICKERS)} tickers...")
main_logger.info(f"Date range: {start_date_str} to {end_date_str}")

for i, ticker_symbol in enumerate(TICKERS):
    main_logger.info(f"\nProcessing ticker {i+1}/{len(TICKERS)}: {ticker_symbol}")
    try:
        # הורדת נתונים עבור הסמל הנוכחי
        # הסרנו את show_errors=True
        ticker_data = yf.download(ticker_symbol, 
                                  start=start_date_str, 
                                  end=end_date_str,
                                  progress=False) # progress=False זה בסדר

        if ticker_data.empty:
            main_logger.warning(f"  No data found for {ticker_symbol} in the given date range by yfinance.")
            # yfinance ידפיס שגיאות רלוונטיות אם יש בעיה עם הסמל
            continue

        ticker_data['Ticker'] = ticker_symbol
        ticker_data.reset_index(inplace=True)
        
        if all_stocks_data.empty:
            all_stocks_data = ticker_data
        else:
            all_stocks_data = pd.concat([all_stocks_data, ticker_data], ignore_index=True)
        
        main_logger.info(f"  Successfully downloaded {len(ticker_data)} data points for {ticker_symbol}.")

    except Exception as e:
        # שגיאות כלליות יותר שלא נתפסו על ידי yfinance עצמו
        main_logger.error(f"  An unexpected error occurred while processing {ticker_symbol}: {e}")
    
    time.sleep(0.5) 

if not all_stocks_data.empty:
    desired_columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    existing_desired_columns = [col for col in desired_columns if col in all_stocks_data.columns]
    all_stocks_data = all_stocks_data[existing_desired_columns]

    try:
        all_stocks_data.to_csv(output_filename, index=False, encoding='utf-8-sig')
        main_logger.info(f"\nHistorical data for all tickers saved to: {output_filename}")
        main_logger.info(f"Total rows in combined CSV: {len(all_stocks_data)}")

        if EMAIL_SENDER_AVAILABLE:
            email_subject = f"Sentibot - Historical Prices Data ({end_date_str})"
            email_body = (
                f"Historical price data collection finished for {len(TICKERS)} tickers.\n"
                f"Date range: {start_date_str} to {end_date_str}.\n\n"
                f"The data is attached as '{output_filename}'.\n\n"
                f"Total rows: {len(all_stocks_data)}\n\n"
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
    main_logger.warning("\nNo data was downloaded for any ticker. Output file not created, and no email sent.")

main_logger.info("Script finished.")
