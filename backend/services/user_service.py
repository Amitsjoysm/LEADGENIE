from fastapi import HTTPException, status
from database import get_db
from models import User, UserUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    async def get_all_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None) -> List[User]:
        """Get all users with pagination"""
        try:
            query = {}
            if role:
                query['role'] = role
            
            cursor = self.db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            return [User(**user) for user in users]
            
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users"
            )
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        try:
            user_doc = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return User(**user_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user by ID error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user"
            )
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        """Update user details"""
        try:
            # Check if user exists
            user_doc = await self.db.users.find_one({"id": user_id})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Prepare update data
            update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}
            
            if update_data:
                await self.db.users.update_one(
                    {"id": user_id},
                    {"$set": update_data}
                )
            
            # Return updated user
            updated_user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            return User(**updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            result = await self.db.users.delete_one({"id": user_id})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    
    async def add_credits(self, user_id: str, credits: int) -> User:
        """Add credits to user"""
        try:
            await self.db.users.update_one(
                {"id": user_id},
                {"$inc": {"credits": credits}}
            )
            
            updated_user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return User(**updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Add credits error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add credits"
            )
    
    async def deduct_credits(self, user_id: str, credits: int) -> User:
        """Deduct credits from user"""
        try:
            # Check if user has enough credits
            user_doc = await self.db.users.find_one({"id": user_id})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user_doc.get('credits', 0) < credits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient credits"
                )
            
            await self.db.users.update_one(
                {"id": user_id},
                {"$inc": {"credits": -credits}}
            )
            
            updated_user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            return User(**updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Deduct credits error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deduct credits"
            )

user_service = UserService()
