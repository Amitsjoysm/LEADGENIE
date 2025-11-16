import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Config(BaseSettings):
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'leadgen_db')
    
    # Redis
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    
    # Email
    SMTP_HOST: str = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_EMAIL: str = os.environ.get('SMTP_EMAIL', '')
    SMTP_PASSWORD: str = os.environ.get('SMTP_PASSWORD', '')
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Credits
    EMAIL_REVEAL_COST: int = 1
    PHONE_REVEAL_COST: int = 3
    
    # Encryption
    ENCRYPTION_KEY: str = os.environ.get('ENCRYPTION_KEY', 'change-this-key-in-production')
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))
    
    # CORS
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    class Config:
        env_file = '.env'

config = Config()
