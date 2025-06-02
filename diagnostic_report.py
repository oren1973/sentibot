import pandas as pd
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe
from email_sender import send_email_with_attachment
from settings import NEWS_SOURCES  # ✅ ייבוא נכון

def get_source_weight(source):
    return NEWS_SOURCES.get(source, {}).get("weight", 1.0)

def generate_diagnostic_report():
    symbols = get_smart_universe()
    rows = []

    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol}")
        headlines = fetch_news_titles(symbol)

        for title, source in headlines:
            score = analyze_sentiment(title, source)
            weight = get_source_weight(source)
            rows.append({
                "symbol": symbol,
                "source": source,
                "headline": title,
                "sentiment_score": score,
                "source_weight": weight,
                "weighted_score": round(score * weight, 4)
            })

    df = pd.DataFrame(rows)
    if df.empty:
        print("⚠️ No data collected.")
        return

    # סיכום לפי מניה
    summary = df.groupby("symbol").apply(lambda g: pd.Series({
        "num_titles": len(g),
        "avg_sentiment": round(g["sentiment_score"].mean(), 4),
        "weighted_avg_sentiment": round(g["weighted_score"].sum() / g["source_weight"].sum(), 4)
    })).reset_index()

    # שמירה לקבצים
    full_output = "diagnostic_report.csv"
    summary_output = "diagnostic_summary.csv"
    df.to_csv(full_output, index=False)
    summary.to_csv(summary_output, index=False)

    print(f"\n📁 Saved full report: {full_output}")
    print(f"📊 Saved summary: {summary_output}")

    # שליחת דוח למייל
    send_email_with_attachment(
        subject="📊 Sentibot – Diagnostic Report",
        body="מצורפים שני דוחות: המלא והמסכם.",
        attachment_path=full_output
    )
    send_email_with_attachment(
        subject="📊 Sentibot – Diagnostic Summary",
        body="מצורף דוח סיכום רגשי לפי מניה.",
        attachment_path=summary_output
    )

if __name__ == "__main__":
    generate_diagnostic_report()
