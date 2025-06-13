# email_sender.py
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from settings import setup_logger 

logger = setup_logger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 

def _check_email_credentials():
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = os.getenv("EMAIL_RECEIVER") 

    if not all([sender, password, receiver]):
        logger.error("Email credentials (EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER) are not fully set in environment variables. Email cannot be sent.")
        return None, None, None
    return sender, password, receiver

# שים לב לשינוי: attachment_path -> attachment_paths (רשימה)
def send_email(subject: str, body: str, receiver_email: str = None, attachment_paths: list = None) -> bool:
    sender, password, default_receiver = _check_email_credentials()
    if not sender: 
        return False

    actual_receiver = receiver_email if receiver_email else default_receiver
    if not actual_receiver: 
        logger.error("No receiver email specified and no default EMAIL_RECEIVER set.")
        return False

    attachment_names = [os.path.basename(p) for p in attachment_paths] if attachment_paths else ['None']
    logger.info(f"Preparing to send email. Subject: '{subject}', To: '{actual_receiver}', Attachments: {', '.join(attachment_names)}")

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = actual_receiver 
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8")) 

        if attachment_paths: # אם יש רשימה של נתיבים
            for attachment_path in attachment_paths: # עבור על כל נתיב
                if attachment_path and os.path.exists(attachment_path):
                    try:
                        with open(attachment_path, "rb") as attachment_file:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment_file.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(attachment_path)
                        part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"") 
                        msg.attach(part)
                        logger.debug(f"Attachment '{filename}' added to email.")
                    except Exception as e_attach:
                        logger.error(f"Failed to attach file '{attachment_path}': {e_attach}")
                elif attachment_path: # אם הנתיב סופק אך לא קיים
                    logger.warning(f"Attachment path '{attachment_path}' does not exist. It will not be attached.")
    
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=20) as server: 
            logger.debug(f"Logging in to SMTP server {SMTP_SERVER} as {sender}...")
            server.login(sender, password)
            logger.debug("SMTP login successful.")
            
            receivers_list = [r.strip() for r in actual_receiver.split(',') if r.strip()]
            if not receivers_list:
                logger.error("No valid receivers after splitting. Cannot send email.")
                return False

            server.sendmail(sender, receivers_list, msg.as_string())
            logger.info(f"Email successfully sent to: {', '.join(receivers_list)}. Subject: '{subject}'")
        return True

    except smtplib.SMTPAuthenticationError as smtp_auth_err:
        logger.error(f"SMTP Authentication Error: {smtp_auth_err}. Check EMAIL_USER and EMAIL_PASS.")
    except smtplib.SMTPException as smtp_err: 
        logger.error(f"SMTP Error occurred: {smtp_err}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}", exc_info=True)
    
    return False

# שים לב לשינוי: attachment_path -> attachment_paths (רשימה)
def send_run_success_email(run_id_str: str, attachment_paths: list = None) -> bool:
    logger.info(f"Attempting to send run success email for run ID: {run_id_str}")
    
    num_attachments = len(attachment_paths) if attachment_paths else 0
    attachment_message = f"Please find the {num_attachments} attached report(s) (if any)." if num_attachments > 0 else "No reports were attached for this run."

    subject = f"Sentibot Run ID {run_id_str} Completed Successfully"
    body = (
        f"Run ID {run_id_str} of Sentibot has finished processing.\n\n"
        f"{attachment_message}\n\n"
        f"Best regards,\nSentibot"
    )
    
    return send_email(subject=subject, body=body, attachment_paths=attachment_paths)


if __name__ == "__main__":
    import logging
    test_logger = setup_logger(__name__, level=logging.DEBUG)
    test_logger.info("--- Testing email sending functionality (multiple attachments) ---")
    
    test_run_id = "test_run_multi_attach_67890"
    dummy_attachment_file1 = "dummy_report_A_for_email_test.txt"
    dummy_attachment_file2 = "dummy_report_B_for_email_test.csv"
    dummy_files_to_create = [dummy_attachment_file1, dummy_attachment_file2]
    created_files = []

    try:
        for fname in dummy_files_to_create:
            with open(fname, "w") as f:
                f.write(f"This is a dummy report: {fname}\n")
                f.write(f"Run ID: {test_run_id}\n")
            created_files.append(fname)
        test_logger.debug(f"Created dummy attachments: {', '.join(created_files)}")

        # בדוק עם רשימה של קבצים
        success = send_run_success_email(run_id_str=test_run_id, attachment_paths=created_files)
        
        # בדוק גם עם קובץ אחד (הפונקציה אמורה להתמודד עם זה אם attachment_paths הוא רשימה עם פריט בודד)
        # success_single = send_run_success_email(run_id_str="test_single_attach", attachment_paths=[dummy_attachment_file1])

        if success:
            test_logger.info(f"Test 'send_run_success_email' with multiple attachments was attempted. Check your inbox for run ID {test_run_id}.")
        else:
            test_logger.error(f"Test 'send_run_success_email' failed or credentials were missing for run ID {test_run_id}.")
            
    except Exception as e_test:
        test_logger.error(f"Error during email test setup or execution: {e_test}")
    finally:
        for fname in created_files:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                    test_logger.debug(f"Removed dummy attachment: {fname}")
                except Exception as e_clean:
                    test_logger.warning(f"Could not remove dummy attachment {fname}: {e_clean}")

    test_logger.info("--- Finished email sending test ---")
