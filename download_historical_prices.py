# download_historical_prices.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time # לשליטה על קצב הבקשות

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
start_date = end_date - timedelta(days=3*365) # 3 שנים אחורה (בערך)

# פורמט תאריך לשליפה מ-yfinance
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# DataFrame לאיסוף כל הנתונים
all_stocks_data = pd.DataFrame()

print(f"Starting download of historical data for {len(TICKERS)} tickers...")
print(f"Date range: {start_date_str} to {end_date_str}")

for i, ticker_symbol in enumerate(TICKERS):
    print(f"\nProcessing ticker {i+1}/{len(TICKERS)}: {ticker_symbol}")
    try:
        # הורדת נתונים עבור הסמל הנוכחי
        ticker_data = yf.download(ticker_symbol, 
                                  start=start_date_str, 
                                  end=end_date_str,
                                  progress=False, # כבה את מד ההתקדמות של yfinance
                                  show_errors=True) # הצג שגיאות מ-yfinance

        if ticker_data.empty:
            print(f"  No data found for {ticker_symbol} in the given date range.")
            continue

        # הוסף עמודת סמל כדי שנדע לאיזו מניה שייכים הנתונים
        ticker_data['Ticker'] = ticker_symbol
        
        # איפוס האינדקס כדי שהתאריך יהפוך לעמודה רגילה
        ticker_data.reset_index(inplace=True)
        
        # שנה את שם עמודת התאריך אם צריך (yfinance מחזיר אותה כ-Date)
        # ticker_data.rename(columns={'Date': 'datetime'}, inplace=True) # אם תרצה שם אחיד

        # הוסף את הנתונים של הסמל הנוכחי ל-DataFrame הכללי
        if all_stocks_data.empty:
            all_stocks_data = ticker_data
        else:
            all_stocks_data = pd.concat([all_stocks_data, ticker_data], ignore_index=True)
        
        print(f"  Successfully downloaded {len(ticker_data)} data points for {ticker_symbol}.")

    except Exception as e:
        print(f"  An error occurred while downloading data for {ticker_symbol}: {e}")
    
    # הוסף השהיה קטנה בין בקשות כדי לא להעמיס על השרת של יאהו
    time.sleep(0.5) # חצי שנייה השהיה

if not all_stocks_data.empty:
    # סדר את העמודות (אופציונלי, לאסתטיקה)
    desired_columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    # ודא שכל העמודות הרצויות קיימות לפני סידור מחדש
    existing_desired_columns = [col for col in desired_columns if col in all_stocks_data.columns]
    all_stocks_data = all_stocks_data[existing_desired_columns]

    # שמור את ה-DataFrame המאוחד לקובץ CSV
    output_filename = "historical_prices_sentiment_universe.csv"
    all_stocks_data.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\nHistorical data for all tickers saved to: {output_filename}")
    print(f"Total rows in combined CSV: {len(all_stocks_data)}")
else:
    print("\nNo data was downloaded for any ticker. Output file not created.")

print("Script finished.")
