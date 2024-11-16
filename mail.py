import os
import smtplib
import logging
from email.mime.text import MIMEText

log = logging.getLogger(os.getenv('APP_NAME'))


def send_email(subject, body):
    try:
        FROM_EMAIL = "yourcstm_tech@outlook.com"
        FROM_EMAIL_PASSWORD = os.getenv("email_password")
        TO_EMAIL = "bythetort@gmail.com"

        # Create the message
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject

        # Connect to the server and sending email
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()
            server.login(FROM_EMAIL, FROM_EMAIL_PASSWORD)
            server.send_message(message, FROM_EMAIL, TO_EMAIL)
            log.info("Successfully sent email")
    except Exception as exc:
        log.exception(exc)
