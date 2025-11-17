from fastapi import HTTPException, status
from database import get_db, get_shard_key
from models import Company, CompanyCreate, CompanyFilter
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self):
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    def _get_collection_name(self, name: str) -> str:
        """Get sharded collection name based on company name"""
        shard = get_shard_key(name)
        return f'companies_{shard}'
    
    async def find_company_by_domain(self, domain: str) -> Company:
        """Find company by domain across all shards"""
        try:
            # Normalize domain (lowercase, strip)
            domain = domain.lower().strip()
            
            # Check all shards
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'companies_{shard}'
                company_doc = await self.db[collection_name].find_one(
                    {"domain": domain}, 
                    {"_id": 0}
                )
                if company_doc:
                    return Company(**company_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Find company by domain error: {e}")
            return None
    
    async def check_domain_exists(self, domain: str) -> bool:
        """Check if domain already exists in unique_domains collection"""
        try:
            # Normalize domain
            domain = domain.lower().strip()
            
            existing = await self.db.unique_domains.find_one({"domain": domain})
            return existing is not None
            
        except Exception as e:
            logger.error(f"Check domain exists error: {e}")
            return False
    
    async def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company"""
        try:
            collection_name = self._get_collection_name(company_data.name)
            
            company_dict = {
                "id": str(uuid.uuid4()),
                **company_data.dict(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db[collection_name].insert_one(company_dict)
            company_dict.pop('_id', None)
            return Company(**company_dict)
            
        except Exception as e:
            logger.error(f"Create company error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create company"
            )
    
    async def get_companies(self, filters: CompanyFilter) -> Dict[str, Any]:
        """Get companies with filters and pagination"""
        try:
            # Build query
            query = {}
            if filters.name:
                query['name'] = {'$regex': filters.name, '$options': 'i'}
            if filters.industry:
                query['industry'] = {'$regex': filters.industry, '$options': 'i'}
            if filters.revenue:
                query['revenue'] = filters.revenue
            if filters.employee_size:
                query['employee_size'] = filters.employee_size
            if filters.city:
                query['city'] = {'$regex': filters.city, '$options': 'i'}
            if filters.state:
                query['state'] = {'$regex': filters.state, '$options': 'i'}
            if filters.country:
                query['country'] = {'$regex': filters.country, '$options': 'i'}
            
            # Query all shards
            all_companies = []
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'companies_{shard}'
                cursor = self.db[collection_name].find(query, {"_id": 0})
                companies = await cursor.to_list(length=None)
                all_companies.extend(companies)
            
            # Pagination
            total = len(all_companies)
            skip = (filters.page - 1) * filters.page_size
            paginated_companies = all_companies[skip:skip + filters.page_size]
            
            return {
                "total": total,
                "page": filters.page,
                "page_size": filters.page_size,
                "companies": [Company(**c) for c in paginated_companies]
            }
            
        except Exception as e:
            logger.error(f"Get companies error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch companies"
            )
    
    async def get_company_by_id(self, company_id: str) -> Company:
        """Get company by ID"""
        try:
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'companies_{shard}'
                company_doc = await self.db[collection_name].find_one({"id": company_id}, {"_id": 0})
                if company_doc:
                    return Company(**company_doc)
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get company by ID error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch company"
            )
    
    async def update_company(self, company_id: str, update_data: dict) -> Company:
        """Update company"""
        try:
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'companies_{shard}'
                company_doc = await self.db[collection_name].find_one({"id": company_id})
                if company_doc:
                    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                    await self.db[collection_name].update_one(
                        {"id": company_id},
                        {"$set": update_data}
                    )
                    updated_company = await self.db[collection_name].find_one({"id": company_id}, {"_id": 0})
                    return Company(**updated_company)
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update company error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update company"
            )
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete company"""
        try:
            shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
            
            for shard in shards:
                collection_name = f'companies_{shard}'
                result = await self.db[collection_name].delete_one({"id": company_id})
                if result.deleted_count > 0:
                    return True
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete company error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete company"
            )

company_service = CompanyService()
