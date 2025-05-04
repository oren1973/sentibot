import os
from sentiment import analyze_sentiment
from trader import execute_trades

print("✅ Sentibot starting...")

headlines = analyze_sentiment()
print(f"DEBUG | headlines found: {len(headlines)}")

execute_trades(headlines)
