import jwt
import hashlib
import secrets
import base64
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from config import config
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Fernet cipher for encryption
def get_fernet_cipher():
    """Get Fernet cipher from config encryption key"""
    key = config.ENCRYPTION_KEY.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'leadgen_salt_2025',
        iterations=100000,
        backend=default_backend()
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(key))
    return Fernet(derived_key)

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

def generate_reset_token() -> str:
    """Generate secure password reset token"""
    return secrets.token_urlsafe(32)

def create_password_reset_token(email: str) -> str:
    """Create password reset token with expiration"""
    token = generate_reset_token()
    return token

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using Fernet"""
    if not data:
        return ""
    try:
        cipher = get_fernet_cipher()
        return cipher.encrypt(data.encode()).decode()
    except Exception:
        return data

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return ""
    try:
        cipher = get_fernet_cipher()
        return cipher.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return encrypted_data

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
