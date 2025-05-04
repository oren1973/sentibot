import requests
from bs4 import BeautifulSoup


def scan_market_and_generate_report():
    url = "https://www.bizportal.co.il/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ שגיאה בגישה לאתר Bizportal: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # חפש בלוקים של חדשות - עדכון לפי המבנה הנוכחי של האתר
    headline_tags = soup.select(".hpArticleTitle a")
    
    if not headline_tags:
        print("⚠️ לא נמצאו כותרות – ודא שמבנה האתר לא השתנה.")

    headlines = []
    for tag in headline_tags:
        text = tag.get_text(strip=True)
        if text:
            headlines.append(text)

    print(f"✅ סריקת שוק הושלמה. נמצאו {len(headlines)} כותרות.")
    return headlines
