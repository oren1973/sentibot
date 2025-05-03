import requests
from bs4 import BeautifulSoup

def scan_market_and_generate_report():
    url = "https://www.bizportal.co.il"
    response = requests.get(url)
    if response.status_code != 200:
        print("DEBUG | Failed to fetch site. Status:", response.status_code)
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.find_all("h3")

    print("DEBUG | headlines found:", len(headlines))
    print("DEBUG | full HTML:", soup.prettify()[:1000])  # הדפסת התחלה לבדיקה

    if not headlines:
        return None

    report = "\n".join(h.get_text(strip=True) for h in headlines if h.get_text(strip=True))
    return report if report.strip() else None
