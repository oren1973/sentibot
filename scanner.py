import requests
from bs4 import BeautifulSoup

def scan_market_and_generate_report():
    url = "https://www.bizportal.co.il/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ שגיאה בגישה לאתר: {e}")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    headlines = soup.find_all("h2")  # ניתן לשנות לפי מבנה האתר

    if not headlines:
        print("DEBUG | headlines found: 0")
        print("DEBUG | full HTML:", response.text[:1000])  # הדפסת תחילת HTML
        return ""

    report_lines = ["🔎 חדשות שוק ההון - כותרות מביזפורטל:\n"]
    for h in headlines[:5]:
        text = h.get_text(strip=True)
        if text:
            report_lines.append(f"• {text}")

    return "\n".join(report_lines)
