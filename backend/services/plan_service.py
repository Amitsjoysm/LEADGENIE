from fastapi import HTTPException, status
from database import get_db
from models import Plan, PlanCreate
from typing import List
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class PlanService:
    def __init__(self):
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    async def create_plan(self, plan_data: PlanCreate) -> Plan:
        """Create a new plan"""
        try:
            plan_dict = {
                "id": str(uuid.uuid4()),
                **plan_data.dict(),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.plans.insert_one(plan_dict)
            plan_dict.pop('_id', None)
            return Plan(**plan_dict)
            
        except Exception as e:
            logger.error(f"Create plan error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create plan"
            )
    
    async def get_all_plans(self, active_only: bool = True) -> List[Plan]:
        """Get all plans"""
        try:
            query = {"is_active": True} if active_only else {}
            cursor = self.db.plans.find(query, {"_id": 0})
            plans = await cursor.to_list(length=None)
            return [Plan(**plan) for plan in plans]
            
        except Exception as e:
            logger.error(f"Get plans error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch plans"
            )
    
    async def get_plan_by_id(self, plan_id: str) -> Plan:
        """Get plan by ID"""
        try:
            plan_doc = await self.db.plans.find_one({"id": plan_id}, {"_id": 0})
            if not plan_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found"
                )
            return Plan(**plan_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get plan by ID error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch plan"
            )
    
    async def update_plan(self, plan_id: str, update_data: dict) -> Plan:
        """Update plan"""
        try:
            result = await self.db.plans.update_one(
                {"id": plan_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found"
                )
            
            updated_plan = await self.db.plans.find_one({"id": plan_id}, {"_id": 0})
            return Plan(**updated_plan)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update plan error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update plan"
            )
    
    async def delete_plan(self, plan_id: str) -> bool:
        """Delete plan (soft delete)"""
        try:
            result = await self.db.plans.update_one(
                {"id": plan_id},
                {"$set": {"is_active": False}}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found"
                )
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete plan error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete plan"
            )

plan_service = PlanService()
