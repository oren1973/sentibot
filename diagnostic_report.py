import pandas as pd
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe

def generate_diagnostic_report():
    symbols = get_smart_universe()
    report_rows = []

    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol}")
        headlines = fetch_news_titles(symbol)

        for title, source in headlines:
            score = analyze_sentiment(title, source)
            report_rows.append({
                "symbol": symbol,
                "source": source,
                "headline": title,
                "sentiment_score": score,
                "source_weight": get_source_weight(source),
                "weighted_score": round(score, 3)
            })

    df = pd.DataFrame(report_rows)
    output_file = "diagnostic_report.csv"
    df.to_csv(output_file, index=False)
    print(f"\n📁 Diagnostic report saved to {output_file}")
    return df

def get_source_weight(source):
    from config import NEWS_SOURCES
    if source in NEWS_SOURCES:
        return NEWS_SOURCES[source].get("weight", 1.0)
    return 1.0

if __name__ == "__main__":
    generate_diagnostic_report()
