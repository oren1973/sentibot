import feedparser

CNBC_RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"

# מיפוי סימבולים לשמות ומילות מפתח
KEYWORDS = {
    "TSLA": ["Tesla", "Elon Musk", "TSLA"],
    "NVDA": ["Nvidia", "Jensen Huang", "NVDA"],
    "GME": ["GameStop", "GME"],
    "AMC": ["AMC", "AMC Entertainment"],
    "PLTR": ["Palantir", "PLTR"],
    "COIN": ["Coinbase", "COIN"],
    "MSTR": ["MicroStrategy", "MSTR", "Saylor"],
    "BYND": ["Beyond Meat", "BYND"],
    "RIVN": ["Rivian", "RIVN"],
    "AFRM": ["Affirm", "AFRM"],
    "SOFI": ["SoFi", "SOFI"],
    "BB": ["BlackBerry", "BB"],
    "BBBYQ": ["Bed Bath", "BBBYQ"],
    "NIO": ["NIO Inc", "NIO"],
    "LCID": ["Lucid", "Lucid Motors", "LCID"],
    "NKLA": ["Nikola", "NKLA"],
    "AAPL": ["Apple", "AAPL", "iPhone"],
    "META": ["Meta", "Facebook", "META"],
    "SNAP": ["Snap", "Snapchat", "SNAP"]
}

def get_cnbc_titles(symbol):
    symbol = symbol.upper()
    keywords = KEYWORDS.get(symbol, [symbol])
    headlines = []

    try:
        feed = feedparser.parse(CNBC_RSS_URL)

        if feed.bozo:
            print(f"⚠️ CNBC RSS parsing error: {feed.bozo_exception}")
            return []

        print(f"\n📰 CNBC headlines scanned for {symbol}:")
        for entry in feed.entries[:30]:  # נרחיב מעט
            title = entry.get("title", "").strip()
            if not title:
                continue

            print(f"- {title}")  # DEBUG: הצגת כל כותרת שנסרקה

            # בדיקת התאמה לפי מילת מפתח
            if any(kw.lower() in title.lower() for kw in keywords):
                headlines.append((title, "CNBC"))

    except Exception as e:
        print(f"⚠️ Error in get_cnbc_titles({symbol}): {e}")

    return headlines
