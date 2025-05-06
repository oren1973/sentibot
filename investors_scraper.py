import requests
from bs4 import BeautifulSoup

def fetch_investors_titles(symbol):
    try:
        url = f"https://www.investors.com/stock-quotes/{symbol.lower()}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        headlines = []
        for item in soup.find_all("a", class_="headline"):
            text = item.get_text(strip=True)
            if text:
                headlines.append(text)

        return headlines

    except Exception as e:
        print(f"⚠️ שגיאה בשליפת חדשות Investors.com עבור {symbol}: {e}")
        return []
