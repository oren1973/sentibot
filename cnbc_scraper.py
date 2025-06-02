import feedparser

CNBC_RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"

# מילון מיפוי בין סימבול למילות מפתח שעשויות להופיע בכותרות
KEYWORDS = {
    "TSLA": ["TSLA", "Tesla", "Elon Musk"],
    "NVDA": ["NVDA", "Nvidia", "Jensen Huang"],
    "GME": ["GME", "GameStop"],
    "AMC": ["AMC", "AMC Entertainment"],
    "PLTR": ["PLTR", "Palantir"],
    "COIN": ["COIN", "Coinbase"],
    "MSTR": ["MSTR", "MicroStrategy", "Saylor"],
    "BYND": ["BYND", "Beyond Meat"],
    "RIVN": ["RIVN", "Rivian"],
    "AFRM": ["AFRM", "Affirm"],
    "SOFI": ["SOFI", "SoFi"],
    "BB": ["BB", "BlackBerry"],
    "BBBYQ": ["BBBYQ", "Bed Bath"],
    "NIO": ["NIO", "NIO Inc"],
    "LCID": ["LCID", "Lucid"],
    "NKLA": ["NKLA", "Nikola"],
    "AAPL": ["AAPL", "Apple", "iPhone"],
    "META": ["META", "Meta", "Facebook", "Mark Zuckerberg"],
    "SNAP": ["SNAP", "Snapchat", "Snap"]
}

def get_cnbc_titles(symbol):
    symbol = symbol.upper()
    keywords = KEYWORDS.get(symbol, [symbol])
    headlines = []

    try:
        feed = feedparser.parse(CNBC_RSS_URL)

        if feed.bozo:
            print(f"⚠️ שגיאה ב־CNBC RSS: {feed.bozo_exception}")
            return []

        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            if any(kw.lower() in title.lower() for kw in keywords):
                headlines.append((title, "CNBC"))

    except Exception as e:
        print(f"⚠️ שגיאה ב־get_cnbc_titles({symbol}): {e}")

    return headlines
