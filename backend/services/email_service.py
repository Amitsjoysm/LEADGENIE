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
        reset_url = f"{config.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "LeadGen Pro - Password Reset Request"
        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>You requested to reset your password for your LeadGen Pro account. Click the button below to proceed:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                        <p><strong>This link will expire in 1 hour.</strong></p>
                        <p>If you didn't request this, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 LeadGen Pro. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, is_html=True)
    
    async def send_welcome_email(self, to_email: str, full_name: str):
        """Send welcome email to new users"""
        subject = "Welcome to LeadGen Pro!"
        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to LeadGen Pro!</h1>
                    </div>
                    <div class="content">
                        <p>Hi {full_name},</p>
                        <p>Thank you for joining LeadGen Pro! We're excited to help you discover quality B2B leads for your business.</p>
                        <p><strong>You've received 10 free credits to get started!</strong></p>
                        <ul>
                            <li>1 credit = Reveal 1 email address</li>
                            <li>3 credits = Reveal 1 phone number</li>
                        </ul>
                        <p>Start exploring our database of 200M+ profiles to find your perfect leads.</p>
                        <p>If you have any questions, don't hesitate to reach out to our support team.</p>
                        <p>Happy lead hunting!</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 LeadGen Pro. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, is_html=True)

email_service = EmailService()
