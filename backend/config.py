import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Config:
    # MongoDB
    MONGO_URL = os.environ['MONGO_URL']
    DB_NAME = os.environ['DB_NAME']
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    # Email
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    
    # Credits
    EMAIL_REVEAL_COST = 1
    PHONE_REVEAL_COST = 3
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

config = Config()
