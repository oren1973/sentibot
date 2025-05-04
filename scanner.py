# scanner.py

import requests
from bs4 import BeautifulSoup

def scan_market_and_generate_report():
    url = "https://finance.yahoo.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print("⚠️ שגיאה בגישה לאתר Yahoo Finance:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    headlines = []

    # מחפש כותרות מהאלמנטים המרכזיים באתר
    for tag in soup.find_all("a"):
        text = tag.get_text(strip=True)
        if text and 20 < len(text) < 150:
            headlines.append(text)

    if not headlines:
        print("⚠️ לא נמצאו כותרות – ודא ששינית את האתר הנסרק.")
    else:
        print(f"DEBUG | headlines found: {len(headlines)}")
        print("DEBUG | first headlines:", headlines[:3])

    return headlines
