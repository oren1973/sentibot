# diagnostic_report.py – ניתוח רגשי + יצוא כותרות לפי מקור

import pandas as pd
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe
from datetime import datetime
import os

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M")
SUMMARY_OUTPUT = "diagnostic_summary.csv"
REPORT_OUTPUT = "diagnostic_report.csv"
TITLES_OUTPUT = "diagnostic_titles.csv"

symbols = get_smart_universe()
all_rows = []

for symbol in symbols:
    titles = fetch_news_titles(symbol)
    for title, source in titles:
        sentiment = analyze_sentiment(title, source)
        all_rows.append({
            "symbol": symbol,
            "headline": title,
            "source": source,
            "sentiment": sentiment
        })

df = pd.DataFrame(all_rows)

df.to_csv(REPORT_OUTPUT, index=False)
print(f"📄 Saved full report: {REPORT_OUTPUT}")

summary = df.groupby("symbol").agg(
    avg_sentiment=("sentiment", "mean"),
    num_titles=("headline", "count")
).reset_index()
summary.to_csv(SUMMARY_OUTPUT, index=False)
print(f"📊 Saved summary: {SUMMARY_OUTPUT}")

titles_by_symbol = df.groupby("symbol").apply(
    lambda g: " | ".join(f"[{src}] {title}" for title, src in zip(g["headline"], g["source"]))
).reset_index().rename(columns={0: "titles"})
titles_by_symbol.to_csv(TITLES_OUTPUT, index=False)
print(f"📝 Saved titles overview: {TITLES_OUTPUT}")
