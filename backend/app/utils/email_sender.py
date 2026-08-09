import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP code to the recipient email.
    If SMTP credentials are set in environment, sends real email via SMTP.
    Otherwise, logs to output for development/testing.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SMTP_SENDER", smtp_user or "noreply@pillsync.com")

    subject = "PillSync - Password Reset OTP"
    body = (
        f"Hello,\n\n"
        f"Your 6-digit OTP for resetting your PillSync password is: {otp_code}\n\n"
        f"This OTP is valid for 10 minutes. If you did not request a password reset, please ignore this email.\n\n"
        f"Stay Healthy,\n"
        f"The PillSync Team"
    )

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(smtp_host, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            import logging
            logger = logging.getLogger("EMAIL_SENDER")
            logger.info(f"[SMTP] OTP email successfully sent to {to_email}")
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger("EMAIL_SENDER")
            logger.warning(f"[SMTP Error] Failed to send email via SMTP: {e}. Falling back to dev logger.")
    
    import logging
    logger = logging.getLogger("EMAIL_SENDER")
    logger.info(f"[DEV LOG] OTP for {to_email}: {otp_code}")
    return True
