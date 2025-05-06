import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from sentiment import clean_text

def fetch_cnbc_titles(symbol):
    base_url = f"https://www.cnbc.com/search/?query={quote(symbol)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ שגיאה בשליפת חדשות CNBC עבור {symbol}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("a", class_="SearchResultCard-headline")

    titles = []
    for article in articles:
        title = article.get_text(strip=True)
        cleaned = clean_text(title)
        titles.append((cleaned, "[CNBC]"))

    return titles
