from motor.motor_asyncio import AsyncIOMotorClient
from config import config
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

def get_shard_key(name: str) -> str:
    """Get shard suffix based on first letter of name"""
    if not name:
        return 'other'
    first_letter = name[0].lower()
    if first_letter.isalpha():
        return first_letter
    return 'other'

async def connect_db():
    """Connect to MongoDB and create indexes"""
    try:
        Database.client = AsyncIOMotorClient(config.MONGO_URL)
        Database.db = Database.client[config.DB_NAME]
        
        # Test connection
        await Database.client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {config.DB_NAME}")
        
        # Create indexes for faster queries
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def create_indexes():
    """Create indexes for all sharded collections"""
    try:
        # User collection indexes
        await Database.db.users.create_index('email', unique=True)
        await Database.db.users.create_index('role')
        
        # Password reset tokens
        await Database.db.password_reset_tokens.create_index('token', unique=True)
        await Database.db.password_reset_tokens.create_index('expires_at')
        
        # Plans
        await Database.db.plans.create_index('is_active')
        
        # UNIQUENESS TRACKING COLLECTIONS (non-sharded for global uniqueness)
        # Unique emails - tracks all profile emails globally
        await Database.db.unique_emails.create_index('email', unique=True)
        await Database.db.unique_emails.create_index('profile_id')
        
        # Unique domains - tracks all company domains globally
        await Database.db.unique_domains.create_index('domain', unique=True)
        await Database.db.unique_domains.create_index('company_id')
        
        # Create indexes for sharded profile collections (a-z + other)
        shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
        
        for shard in shards:
            profile_collection = f'profiles_{shard}'
            company_collection = f'companies_{shard}'
            
            # Profile indexes
            await Database.db[profile_collection].create_index('first_name')
            await Database.db[profile_collection].create_index('last_name')
            await Database.db[profile_collection].create_index('job_title')
            await Database.db[profile_collection].create_index('industry')
            await Database.db[profile_collection].create_index('company_name')
            await Database.db[profile_collection].create_index('company_id')  # NEW: Link to company
            await Database.db[profile_collection].create_index('country')
            await Database.db[profile_collection].create_index([('first_name', 'text'), ('last_name', 'text'), ('job_title', 'text')])
            
            # Company indexes
            await Database.db[company_collection].create_index('name')
            await Database.db[company_collection].create_index('domain')  # For domain lookups
            await Database.db[company_collection].create_index('industry')
            await Database.db[company_collection].create_index('employee_size')
            await Database.db[company_collection].create_index('country')
            await Database.db[company_collection].create_index([('name', 'text'), ('description', 'text')])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

async def close_db():
    """Close database connection"""
    if Database.client:
        Database.client.close()
        logger.info("Closed MongoDB connection")

def get_db():
    return Database.db
