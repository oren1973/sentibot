import os
import requests

# שליפת מפתחות מהסביבה
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

print("📡 בודק חיבור ל-Alpaca...")

# בדיקת חיבור לחשבון
r = requests.get(f"{BASE_URL}/v2/account", headers=headers)
if r.status_code == 200:
    print("✅ חיבור ל-Alpaca הצליח!")
else:
    print(f"❌ חיבור נכשל: {r.status_code} {r.text}")
    exit()

# בדיקת זמינות של מניית META
symbol = "META"
print(f"\n🔍 בודק אם {symbol} קיימת וניתנת למסחר...")

r = requests.get(f"{BASE_URL}/v2/assets/{symbol}", headers=headers)
if r.status_code == 200:
    data = r.json()
    tradable = data.get("tradable", False)
    easy_to_borrow = data.get("easy_to_borrow", False)
    print(f"📈 {symbol} קיימת במערכת!")
    print(f"🛒 ניתן לסחור בה? {'✅ כן' if tradable else '❌ לא'}")
    print(f"💵 ניתן לשאול אותה? {'✅ כן' if easy_to_borrow else '❌ לא'}")
else:
    print(f"❌ לא ניתן לבדוק את {symbol}: {r.status_code} {r.text}")
