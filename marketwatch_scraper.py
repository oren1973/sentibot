import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from sentiment import clean_text

def fetch_marketwatch_titles(symbol):
    try:
        base_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        headlines = soup.select("h3.article__headline, h4.article__headline")

        titles = [clean_text(h.get_text(strip=True)) for h in headlines if h.get_text(strip=True)]
        return titles[:10]

    except Exception as e:
        print(f"⚠️ שגיאה בשליפת חדשות MarketWatch עבור {symbol}: {e}")
        return []
