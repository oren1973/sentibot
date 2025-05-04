# 📄 scanner.py
import requests
from bs4 import BeautifulSoup

def scan_market_headlines():
    urls = [
        "https://www.marketwatch.com/latest-news",
        "https://www.investors.com/news/",
        "https://www.bloomberg.com/markets"
    ]

    headlines = []

    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup.find_all(["h3", "h2", "a"]):
                text = tag.get_text(strip=True)
                if text and 10 < len(text) < 200:
                    headlines.append(text)
        except Exception as e:
            print(f"⚠️ Failed to fetch from {url}:", e)

    return headlines
