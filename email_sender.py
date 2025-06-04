# email_sender.py
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from settings import setup_logger # ייבוא מהקובץ settings.py

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "email_sender"

# --- פרטי שרת SMTP (עבור Gmail) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # עבור SSL

def _check_email_credentials():
    """בודק אם פרטי המייל החיוניים מוגדרים במשתני הסביבה."""
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = os.getenv("EMAIL_RECEIVER") # אפשר לתמוך במספר נמענים מופרדים בפסיק

    if not all([sender, password, receiver]):
        logger.error("Email credentials (EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER) are not fully set in environment variables. Email cannot be sent.")
        return None, None, None
    return sender, password, receiver

def send_email(subject: str, body: str, receiver_email: str = None, attachment_path: str = None) -> bool:
    """
    פונקציה גנרית לשליחת מייל עם אפשרות לקובץ מצורף.
    מחזירה True אם השליחה הצליחה (לפחות ניסיון השליחה), False אחרת.
    """
    sender, password, default_receiver = _check_email_credentials()
    if not sender: # אם הפרטים חסרים
        return False

    # השתמש בנמען שסופק, או בנמען ברירת המחדל אם לא סופק
    actual_receiver = receiver_email if receiver_email else default_receiver
    if not actual_receiver: # אם גם הנמען הספציפי וגם ברירת המחדל חסרים
        logger.error("No receiver email specified and no default EMAIL_RECEIVER set.")
        return False

    logger.info(f"Preparing to send email. Subject: '{subject}', To: '{actual_receiver}', Attachment: '{attachment_path or 'None'}'")

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = actual_receiver # יכול להיות רשימה מופרדת בפסיקים של נמענים
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8")) # הגדרת קידוד utf-8 לגוף ההודעה

        if attachment_path:
            if os.path.exists(attachment_path):
                try:
                    with open(attachment_path, "rb") as attachment_file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment_file.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment_path)
                    part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"") # הוספת מרכאות לשם הקובץ
                    msg.attach(part)
                    logger.debug(f"Attachment '{filename}' added to email.")
                except Exception as e_attach:
                    logger.error(f"Failed to attach file '{attachment_path}': {e_attach}")
                    # אפשר להחליט אם לשלוח את המייל בכל זאת בלי הקובץ, או לא לשלוח כלל
                    # כרגע, המייל יישלח בלי הקובץ אם הצירוף נכשל.
            else:
                logger.warning(f"Attachment path '{attachment_path}' does not exist. Email will be sent without attachment.")
    
        # התחברות לשרת ושליחת המייל
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=20) as server: # הוספת timeout לשרת
            logger.debug(f"Logging in to SMTP server {SMTP_SERVER} as {sender}...")
            server.login(sender, password)
            logger.debug("SMTP login successful.")
            
            # תמיכה במספר נמענים (אם actual_receiver הוא מחרוזת מופרדת בפסיקים)
            receivers_list = [r.strip() for r in actual_receiver.split(',') if r.strip()]
            if not receivers_list:
                logger.error("No valid receivers after splitting. Cannot send email.")
                return False

            server.sendmail(sender, receivers_list, msg.as_string())
            logger.info(f"Email successfully sent to: {', '.join(receivers_list)}. Subject: '{subject}'")
        return True

    except smtplib.SMTPAuthenticationError as smtp_auth_err:
        logger.error(f"SMTP Authentication Error: {smtp_auth_err}. Check EMAIL_USER and EMAIL_PASS.")
    except smtplib.SMTPException as smtp_err: # שגיאות SMTP כלליות
        logger.error(f"SMTP Error occurred: {smtp_err}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}", exc_info=True)
    
    return False


# --- פונקציות עטיפה ספציפיות (Wrapper functions) ---
def send_run_success_email(run_id_str: str, attachment_path: str = None) -> bool:
    """
    שולח מייל סיכום הצלחה להרצה.
    """
    logger.info(f"Attempting to send run success email for run ID: {run_id_str}")
    
    subject = f"Sentibot Run ID {run_id_str} Completed Successfully"
    body = (
        f"Run ID {run_id_str} of Sentibot has finished processing.\n\n"
        f"Please find the attached report (if any).\n\n"
        f"Best regards,\nSentibot"
    )
    
    # הנמען יילקח מ-EMAIL_RECEIVER המוגדר בסביבה
    return send_email(subject=subject, body=body, attachment_path=attachment_path)


# הפונקציה send_email_with_attachment המקורית שלך די דומה ל-send_email הגנרית,
# אז אפשר פשוט להשתמש ב-send_email ישירות או ליצור עטיפה אם צריך התנהגות קצת שונה.
# נשאיר אותה כרגע אם יש לך שימוש ספציפי בה, או נסיר אותה אם send_email מספיקה.
# def send_specific_report_email(report_name: str, attachment_path: str):
#     subject = f"Sentibot Report: {report_name}"
#     body = f"Please find the attached Sentibot report: {report_name}."
#     return send_email(subject=subject, body=body, attachment_path=attachment_path)


if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית ---
    # חשוב: ודא שמשתני הסביבה EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER מוגדרים!
    # אם לא, הבדיקה תיכשל בשלב _check_email_credentials.
    import logging
    test_logger = setup_logger(__name__, level=logging.DEBUG)

    test_logger.info("--- Testing email sending functionality ---")
    
    # בדיקת פונקציית העטיפה
    test_run_id = "test_run_12345"
    # צור קובץ דמה לבדיקת צירוף
    dummy_attachment_file = "dummy_report_for_email_test.txt"
    try:
        with open(dummy_attachment_file, "w") as f:
            f.write("This is a dummy report for testing email attachments.\n")
            f.write(f"Run ID: {test_run_id}\n")
        test_logger.debug(f"Created dummy attachment: {dummy_attachment_file}")

        success = send_run_success_email(run_id_str=test_run_id, attachment_path=dummy_attachment_file)
        if success:
            test_logger.info(f"Test 'send_run_success_email' was attempted. Check your inbox for run ID {test_run_id}.")
        else:
            test_logger.error(f"Test 'send_run_success_email' failed or credentials were missing for run ID {test_run_id}.")
    
    except Exception as e_test:
        test_logger.error(f"Error during email test setup or execution: {e_test}")
    finally:
        # נקה את קובץ הדמה
        if os.path.exists(dummy_attachment_file):
            try:
                os.remove(dummy_attachment_file)
                test_logger.debug(f"Removed dummy attachment: {dummy_attachment_file}")
            except Exception as e_clean:
                test_logger.warning(f"Could not remove dummy attachment {dummy_attachment_file}: {e_clean}")

    test_logger.info("--- Finished email sending test ---")
