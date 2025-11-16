import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from config import config
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def encrypt_data(data: str) -> str:
    """Simple encryption for frontend data masking"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def mask_email(email: str) -> str:
    """Mask email for display"""
    if '@' not in email:
        return '***@***.com'
    local, domain = email.split('@')
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[:2]}***@{domain}"

def mask_phone(phone: str) -> str:
    """Mask phone for display"""
    if len(phone) <= 4:
        return '***-***-****'
    return f"***-***-{phone[-4:]}"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone format"""
    pattern = r'^[\d\s\-\+\(\)]+$'
    return bool(re.match(pattern, phone)) and len(re.sub(r'[^\d]', '', phone)) >= 10
