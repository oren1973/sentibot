import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from sentiment import analyze_sentiment

def fetch_cnbc_titles(stock_symbol):
    try:
        search_url = f"https://www.cnbc.com/search/?query={quote(stock_symbol)}"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', class_='SearchResult-searchResultLink', limit=10)
        titles = [a.get_text(strip=True) for a in articles if a.get_text(strip=True)]

        return titles
    except Exception as e:
        print(f"⚠️ שגיאה בשליפת חדשות CNBC עבור {stock_symbol}: {e}")
        return []
