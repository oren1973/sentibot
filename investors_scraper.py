import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.investors.com/etfs-and-funds/sectors/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_investors_titles(symbol):
    try:
        url = f"https://www.investors.com/quotes/{symbol.lower()}"
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"שגיאה בגישה לכתובת {url}: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = []

        # מחפש כותרות חדשות מהעמוד
        for item in soup.select('a.headline'):
            title = item.get_text(strip=True)
            if title:
                headlines.append(title)

        return headlines

    except Exception as e:
        print(f"שגיאה בשליפת כותרות עבור {symbol}: {e}")
        return []

if __name__ == "__main__":
    symbol = "AAPL"  # תוכל לשנות את זה לכל מניה אחרת
    titles = fetch_investors_titles(symbol)
    print(f"כותרות עבור {symbol}:")
    for t in titles:
        print("-", t)
