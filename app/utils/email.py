import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

class EmailService:
    def __init__(self):
        self.host = settings.email_host
        self.port = settings.email_port
        self.user = settings.email_user
        self.password = settings.email_password
        self.sender = settings.email_from

    def send_email(self, to: str, subject: str, html_body: str):
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"]    = self.sender
        msg["To"]      = to

        with smtplib.SMTP(self.host, self.port) as smtp:
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(msg)
