import schedule
import time
import subprocess
from datetime import datetime

def run_main():
    now = datetime.now().strftime('%H:%M:%S')
    print(f"▶️ Running main.py at {now}")
    subprocess.run(["python", "main.py"])

# Schedule: every day at 17:00 Israel time (UTC+3)
schedule.every().day.at("14:00").do(run_main)  # 14:00 UTC = 17:00 IST

print("🕒 Scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(30)
