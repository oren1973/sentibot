import schedule
import time
import subprocess
from datetime import datetime

def run_main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"▶️ {now} – Running main.py...")
    try:
        result = subprocess.run(["python", "main.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("❌ Error:", result.stderr)
    except Exception as e:
        print(f"❌ Failed to run main.py: {e}")

# להרצה כל דקה (לבדיקה)
schedule.every(1).minutes.do(run_main)

print("🕒 Sentibot Scheduler is running... Waiting for next scheduled task.")

while True:
    schedule.run_pending()
    time.sleep(5)
