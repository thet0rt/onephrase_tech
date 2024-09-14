import os
import smtplib
from log_settings import log
from email.mime.text import MIMEText


def send_email(subject, body):
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
