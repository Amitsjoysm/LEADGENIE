import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import config
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_email = config.SMTP_EMAIL
        self.smtp_password = config.SMTP_PASSWORD
    
    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        """Send email using SMTP"""
        try:
            if not self.smtp_email or not self.smtp_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            message = MIMEMultipart()
            message['From'] = self.smtp_email
            message['To'] = to_email
            message['Subject'] = subject
            
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_email,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_password_reset_email(self, to_email: str, reset_token: str):
        """Send password reset email"""
        reset_url = f"https://yourdomain.com/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password. Click the link below to proceed:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, is_html=True)

email_service = EmailService()
