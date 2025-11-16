from fastapi import HTTPException, status
from database import get_db, get_shard_key
from models import Profile, ProfileCreate, ProfileFilter
from utils import mask_email, mask_phone
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self):
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    def _get_collection_name(self, last_name: str) -> str:
        """Get sharded collection name based on last name"""
        shard = get_shard_key(last_name)
        return f'profiles_{shard}'
    
    async def create_profile(self, profile_data: ProfileCreate) -> Profile:
        """Create a new profile"""
        try:
            collection_name = self._get_collection_name(profile_data.last_name)
            
            profile_dict = {
                "id": str(uuid.uuid4()),
                **profile_data.dict(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db[collection_name].insert_one(profile_dict)
            profile_dict.pop('_id', None)
            return Profile(**profile_dict)
            
        except Exception as e:
            logger.error(f"Create profile error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile"
            )
    
    async def get_profiles(self, filters: ProfileFilter, mask_data: bool = True) -> Dict[str, Any]:
        """Get profiles with filters and pagination"""
        try:
            # Build query
            query = {}
            if filters.first_name:
                query['first_name'] = {'$regex': filters.first_name, '$options': 'i'}
            if filters.last_name:
                query['last_name'] = {'$regex': filters.last_name, '$options': 'i'}
            if filters.job_title:
                query['job_title'] = {'$regex': filters.job_title, '$options': 'i'}
            if filters.industry:
                query['industry'] = {'$regex': filters.industry, '$options': 'i'}
            if filters.sub_industry:
                query['sub_industry'] = {'$regex': filters.sub_industry, '$options': 'i'}
            if filters.company_name:
                query['company_name'] = {'$regex': filters.company_name, '$options': 'i'}
            if filters.city:
                query['city'] = {'$regex': filters.city, '$options': 'i'}
            if filters.state:
                query['state'] = {'$regex': filters.state, '$options': 'i'}
            if filters.country:
                query['country'] = {'$regex': filters.country, '$options': 'i'}
            if filters.keywords:
                query['keywords'] = {'$in': filters.keywords}
            
            # Query all shards
            all_profiles = []
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'profiles_{shard}'
                cursor = self.db[collection_name].find(query, {"_id": 0})
                profiles = await cursor.to_list(length=None)
                all_profiles.extend(profiles)
            
            # Pagination
            total = len(all_profiles)
            skip = (filters.page - 1) * filters.page_size
            paginated_profiles = all_profiles[skip:skip + filters.page_size]
            
            # Mask sensitive data if needed
            if mask_data:
                for profile in paginated_profiles:
                    if profile.get('emails'):
                        profile['emails'] = [mask_email(email) for email in profile['emails']]
                    if profile.get('phones'):
                        profile['phones'] = [mask_phone(phone) for phone in profile['phones']]
                    profile['company_domain'] = '***.' + profile.get('company_domain', '').split('.')[-1] if profile.get('company_domain') else None
            
            return {
                "total": total,
                "page": filters.page,
                "page_size": filters.page_size,
                "profiles": [Profile(**p) for p in paginated_profiles]
            }
            
        except Exception as e:
            logger.error(f"Get profiles error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch profiles"
            )
    
    async def get_profile_by_id(self, profile_id: str, mask_data: bool = True) -> Profile:
        """Get profile by ID"""
        try:
            # Search all shards
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'profiles_{shard}'
                profile_doc = await self.db[collection_name].find_one({"id": profile_id}, {"_id": 0})
                if profile_doc:
                    if mask_data:
                        if profile_doc.get('emails'):
                            profile_doc['emails'] = [mask_email(email) for email in profile_doc['emails']]
                        if profile_doc.get('phones'):
                            profile_doc['phones'] = [mask_phone(phone) for phone in profile_doc['phones']]
                    return Profile(**profile_doc)
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get profile by ID error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch profile"
            )
    
    async def update_profile(self, profile_id: str, update_data: dict) -> Profile:
        """Update profile"""
        try:
            # Find profile in shards
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'profiles_{shard}'
                profile_doc = await self.db[collection_name].find_one({"id": profile_id})
                if profile_doc:
                    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                    await self.db[collection_name].update_one(
                        {"id": profile_id},
                        {"$set": update_data}
                    )
                    updated_profile = await self.db[collection_name].find_one({"id": profile_id}, {"_id": 0})
                    return Profile(**updated_profile)
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update profile error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete profile"""
        try:
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'profiles_{shard}'
                result = await self.db[collection_name].delete_one({"id": profile_id})
                if result.deleted_count > 0:
                    return True
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete profile error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete profile"
            )
    
    async def reveal_contact(self, user_id: str, profile_id: str, reveal_type: str) -> Dict[str, Any]:
        """Reveal contact information with credit deduction (atomic and race-condition safe)"""
        from config import config
        try:
            # Check if already revealed
            existing_reveal = await self.db.revealed_contacts.find_one({
                "user_id": user_id,
                "profile_id": profile_id,
                "reveal_type": reveal_type
            })
            
            if existing_reveal:
                # Already revealed - just return the data without charging
                profile = await self.get_profile_by_id(profile_id, mask_data=False)
                user = await self.db.users.find_one({"id": user_id}, {"credits": 1})
                credits_remaining = user.get('credits', 0) if user else 0
                
                if reveal_type == 'email':
                    return {
                        "emails": profile.emails,
                        "already_revealed": True,
                        "credits_remaining": credits_remaining,
                        "credits_used": 0
                    }
                else:
                    return {
                        "phones": profile.phones,
                        "already_revealed": True,
                        "credits_remaining": credits_remaining,
                        "credits_used": 0
                    }
            
            # Calculate cost
            cost = config.EMAIL_REVEAL_COST if reveal_type == 'email' else config.PHONE_REVEAL_COST
            
            # Atomic credit deduction - deduct credits only if user has enough
            # This prevents race conditions by checking and updating in one atomic operation
            updated_user = await self.db.users.find_one_and_update(
                {
                    "id": user_id,
                    "credits": {"$gte": cost}  # Only update if credits >= cost
                },
                {
                    "$inc": {"credits": -cost}
                },
                return_document=True  # Return updated document
            )
            
            # If no user was updated, either user doesn't exist or has insufficient credits
            if not updated_user:
                user = await self.db.users.find_one({"id": user_id})
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient credits. Need {cost} credits, you have {user.get('credits', 0)}."
                    )
            
            credits_remaining = updated_user.get('credits', 0)
            
            # Record reveal (after successful credit deduction)
            reveal_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "profile_id": profile_id,
                "reveal_type": reveal_type,
                "revealed_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await self.db.revealed_contacts.insert_one(reveal_doc)
                
                # Record credit transaction
                transaction_doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "amount": -cost,
                    "transaction_type": f"reveal_{reveal_type}",
                    "reference_id": profile_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.credit_transactions.insert_one(transaction_doc)
                
            except Exception as insert_error:
                # If reveal/transaction recording fails, rollback the credit deduction
                logger.error(f"Failed to record reveal/transaction: {insert_error}. Rolling back credits.")
                await self.db.users.update_one(
                    {"id": user_id},
                    {"$inc": {"credits": cost}}  # Refund credits
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to record reveal. Credits have been refunded."
                )
            
            # Get unmasked profile data
            profile = await self.get_profile_by_id(profile_id, mask_data=False)
            
            if reveal_type == 'email':
                return {
                    "emails": profile.emails,
                    "credits_remaining": credits_remaining,
                    "credits_used": cost,
                    "already_revealed": False
                }
            else:
                return {
                    "phones": profile.phones,
                    "credits_remaining": credits_remaining,
                    "credits_used": cost,
                    "already_revealed": False
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Reveal contact error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reveal contact"
            )

profile_service = ProfileService()
