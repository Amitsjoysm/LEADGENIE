from fastapi import HTTPException, status
from database import get_db
from models import UserCreate, UserLogin, User
from utils import hash_password, verify_password, create_access_token
from datetime import datetime, timezone, timedelta
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await self.db.users.find_one({"email": user_data.email})
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user document
            user_dict = {
                "id": str(uuid.uuid4()),
                "email": user_data.email,
                "password": hash_password(user_data.password),
                "full_name": user_data.full_name,
                "role": user_data.role,
                "credits": 10 if user_data.role == 'user' else 0,  # Welcome credits
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.users.insert_one(user_dict)
            
            # Send welcome email asynchronously
            try:
                from services.email_service import email_service
                asyncio.create_task(email_service.send_welcome_email(user_data.email, user_data.full_name))
            except Exception as e:
                logger.warning(f"Failed to send welcome email: {e}")
            
            # Return user without password
            user_dict.pop('password')
            user_dict.pop('_id', None)
            return User(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def login_user(self, login_data: UserLogin) -> dict:
        """Login user and return token"""
        try:
            # Find user by email
            user_doc = await self.db.users.find_one({"email": login_data.email})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not verify_password(login_data.password, user_doc['password']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user_doc.get('is_active', True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive"
                )
            
            # Create access token
            access_token = create_access_token(data={"sub": user_doc['email']})
            
            # Return user data without password
            user_doc.pop('password')
            user_doc.pop('_id', None)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": User(**user_doc)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        try:
            user_doc = await self.db.users.find_one({"email": email})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_doc.pop('password', None)
            user_doc.pop('_id', None)
            return User(**user_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user"
            )
    
    async def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        try:
            # Check if user exists
            user_doc = await self.db.users.find_one({"email": email})
            if not user_doc:
                # Don't reveal if email exists
                return "token_sent"
            
            # Create reset token
            token = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            reset_doc = {
                "token": token,
                "email": email,
                "expires_at": expires_at.isoformat(),
                "used": False
            }
            
            await self.db.password_reset_tokens.insert_one(reset_doc)
            return token
            
        except Exception as e:
            logger.error(f"Create reset token error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create reset token"
            )
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        try:
            # Find token
            token_doc = await self.db.password_reset_tokens.find_one({"token": token})
            if not token_doc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired token"
                )
            
            # Check if token is used
            if token_doc.get('used', False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token already used"
                )
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_doc['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token expired"
                )
            
            # Update password
            hashed_password = hash_password(new_password)
            await self.db.users.update_one(
                {"email": token_doc['email']},
                {"$set": {"password": hashed_password}}
            )
            
            # Mark token as used
            await self.db.password_reset_tokens.update_one(
                {"token": token},
                {"$set": {"used": True}}
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )

auth_service = AuthService()
