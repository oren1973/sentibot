import os

# בדיקת משתני סביבה
sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("APP_PASSWORD")
receiver_email = os.getenv("RECEIVER_EMAIL")

print("✅ DEBUG | SENDER_EMAIL:", sender_email)
print("✅ DEBUG | APP_PASSWORD is None:", app_password is None)
print("✅ DEBUG | RECEIVER_EMAIL:", receiver_email)

exit(0)
