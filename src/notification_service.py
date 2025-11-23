import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("EMAIL_PORT", 587))
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.alert_email = os.getenv("ALERT_EMAIL")
        
        if not all([self.user, self.password, self.alert_email]):
            print("Warning: Notification credentials missing. Alerts will not be sent.")

    def send_error_alert(self, subject: str, error_message: str, context: str = ""):
        """
        Sends an email alert about an error.
        """
        if not self.alert_email:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = self.alert_email
            msg['Subject'] = f"⚠️ Invoice Automation Error: {subject}"

            body = f"""
            <h2>Invoice Processing Error</h2>
            <p><strong>Context:</strong> {context}</p>
            <p><strong>Error Details:</strong></p>
            <pre>{error_message}</pre>
            <p>Please check the system logs for more information.</p>
            """
            
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
                
            print(f"Error alert sent to {self.alert_email}")
            
        except Exception as e:
            print(f"Failed to send error alert: {e}")
