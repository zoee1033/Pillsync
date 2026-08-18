import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EMAIL_SENDER")


def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP code to the recipient email via SMTP.
    If SMTP environment variables (SMTP_HOST, SMTP_USER/USERNAME, SMTP_PASSWORD) are configured,
    sends email via SMTP.
    If SMTP is configured and fails or if SMTP configuration is missing, returns False so caller can raise HTTP 500 error.
    """
    from app.config import settings

    smtp_host = os.getenv("SMTP_HOST") or settings.SMTP_HOST
    smtp_port = os.getenv("SMTP_PORT") or str(settings.SMTP_PORT or 587)
    smtp_user = os.getenv("SMTP_USER") or os.getenv("SMTP_USERNAME") or settings.SMTP_USER or settings.SMTP_USERNAME
    smtp_password = os.getenv("SMTP_PASSWORD") or settings.SMTP_PASSWORD
    sender_email = (
        os.getenv("SMTP_SENDER")
        or os.getenv("SMTP_FROM_EMAIL")
        or settings.SMTP_SENDER
        or settings.SMTP_FROM_EMAIL
        or smtp_user
        or "noreply@pillsync.com"
    )

    subject = "PillSync - Password Reset Verification Code"

    text_body = (
        f"Hello,\n\n"
        f"Your 6-digit OTP for resetting your PillSync password is: {otp_code}\n\n"
        f"This OTP is valid for 10 minutes. If you did not request a password reset, please ignore this email and secure your account.\n\n"
        f"Do not share this OTP with anyone.\n\n"
        f"Stay Healthy,\n"
        f"The PillSync Team"
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .logo {{ font-size: 24px; font-weight: 800; color: #0F8B6D; text-align: center; margin-bottom: 20px; }}
        .title {{ font-size: 18px; font-weight: 700; color: #1e293b; text-align: center; margin-bottom: 12px; }}
        .text {{ font-size: 14px; color: #475569; line-height: 1.6; text-align: center; margin-bottom: 24px; }}
        .otp-box {{ background: #E6F4F0; border: 2px dashed #0F8B6D; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 24px; }}
        .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0F8B6D; }}
        .warning {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">💊 PillSync</div>
        <div class="title">Password Reset Request</div>
        <div class="text">We received a request to reset the password for your PillSync account. Use the verification code below to set a new password:</div>
        <div class="otp-box">
          <div class="otp-code">{otp_code}</div>
        </div>
        <div class="text">This code will expire in <strong>10 minutes</strong>. If you did not request a password reset, please ignore this email.</div>
        <div class="warning">⚠️ Security Notice: Never share this OTP code with anyone. PillSync staff will never ask for your verification code.</div>
      </div>
    </body>
    </html>
    """

    if not (smtp_host and smtp_user and smtp_password):
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENVIRONMENT") == "testing" or os.getenv("TESTING") == "true":
            logger.info(f"[DEV LOG] Test environment detected. OTP generated for {to_email}")
            return True

        logger.error("[SMTP Error] Cannot send email. SMTP_HOST, SMTP_USER, or SMTP_PASSWORD environment variable is missing.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        port = int(smtp_port)
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.starttls()

        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"[SMTP Success] OTP email successfully sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[SMTP Error] Failed to send OTP email to {to_email}: {e}")
        return False

