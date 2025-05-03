import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scan_market_and_generate_report():
    url = "https://www.bizportal.co.il/"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        headlines = soup.find_all("h3")

        if not headlines:
            return None

        selected = [h.get_text(strip=True) for h in headlines[:5]]
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        report = f"דוח רגשות שוק ({date}):\n" + "\n".join(f"- {line}" for line in selected)
        return report
    except Exception as e:
        return f"שגיאה במהלך סריקת האתר: {e}"
