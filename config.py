# config.py – משתני מערכת, ללא NEWS_SOURCES

import os
from datetime import date

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

LOG_NAME = f"learning_log_{date.today().isoformat()}.csv"
