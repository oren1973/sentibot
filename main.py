# main.py
# Sentibot: Autonomous Emotional Trading Bot (Simulation Mode)
# Version: Stable MVP | Reviewed and Peer-Checked

import requests
from scanner import scan_news
from emailer import send_status_email
from time import sleep
from datetime import datetime

INTERVAL_MINUTES = 60  # Email interval in minutes


def main():
    print("[INFO] Sentibot started at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    while True:
        try:
            print("[INFO] Scanning news...")
            scan_news()

            print("[INFO] Sending status email...")
            send_status_email()

            print(f"[INFO] Sleeping for {INTERVAL_MINUTES} minutes...\n")
            sleep(INTERVAL_MINUTES * 60)

        except Exception as e:
            print("[ERROR] Unexpected error occurred:", e)
            sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    main()
