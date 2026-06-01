import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart


# =====================================================
# EMAIL CONFIG
# =====================================================

EMAIL_ADDRESS = "ummanenibalajirockzz007@gmail.com"

EMAIL_PASSWORD = "mvwl zuta okyj nxwo"


# =====================================================
# SEND RESET EMAIL
# =====================================================

def send_reset_email(
    receiver_email,
    reset_token
):

    reset_link = (
        f"http://localhost:8501/?token={reset_token}"
    )

    subject = "Password Reset Request"

    body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

If you did not request this,
please ignore this email.
"""

    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS

    msg["To"] = receiver_email

    msg["Subject"] = subject

    msg.attach(
        MIMEText(body, "plain")
    )

    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(msg)

        server.quit()

        return True

    except Exception as e:

        print("EMAIL ERROR:", e)

        return False