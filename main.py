import datetime
from config import SYMBOLS, MAX_TITLES_PER_SOURCE
from news_scraper import get_yahoo_news, get_investors_news, get_cnbc_news
from sentiment_analyzer import analyze_sentiment
from recommender import get_recommendation
from alpaca_trader import execute_trade
from mailer import send_run_success_email
from performance_analyzer import update_learning_log, summarize_performance
import pandas as pd
import os

def main():
    run_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"\n🚀 Starting Sentibot run {run_id}")
    run_data = []

    for symbol in SYMBOLS:
        print(f"\n🔍 Processing {symbol}")
        try:
            yahoo_titles = get_yahoo_news(symbol)[:MAX_TITLES_PER_SOURCE]
            investors_titles = get_investors_news(symbol)[:MAX_TITLES_PER_SOURCE]
            cnbc_titles = get_cnbc_news(symbol)[:MAX_TITLES_PER_SOURCE]

            all_titles = yahoo_titles + investors_titles + cnbc_titles
            print(f"📰 Total titles for {symbol}: {len(all_titles)}")

            if not all_titles:
                print(f"⚠️ No titles found for {symbol}. Skipping.")
                continue

            sentiment = analyze_sentiment(all_titles, symbol)
            action = get_recommendation(sentiment)
            trade_result = execute_trade(symbol, action)

            record = {
                "symbol": symbol,
                "sentiment": sentiment,
                "action": action,
                "trade_result": trade_result,
                "run_id": run_id,
                "timestamp": datetime.datetime.now()
            }
            run_data.append(record)

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

    if run_data:
        df = pd.DataFrame(run_data)
        output_path = f"learning_log_full.csv"
        df.to_csv(output_path, mode="a", index=False, header=not os.path.exists(output_path))
        print(f"💾 Results saved to {output_path}")
        update_learning_log(output_path)
        summarize_performance(output_path)
        send_run_success_email(run_id, output_path)
    else:
        print("⚠️ No data to save. Skipping file creation and email.")

if __name__ == "__main__":
    main()
