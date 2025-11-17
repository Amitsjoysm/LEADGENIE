"""
Migration script to add hierarchical relationships and uniqueness tracking
- Links existing profiles to companies via company_id
- Populates unique_emails collection
- Populates unique_domains collection
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'leadgen_db')


async def migrate():
    """Run migration to add company relationships and uniqueness tracking"""
    print("🚀 Starting migration...")
    
    try:
        # Connect to database
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {DB_NAME}")
        
        # Step 1: Migrate companies and populate unique_domains
        print("\n📊 Step 1: Migrating companies...")
        await migrate_companies(db)
        
        # Step 2: Migrate profiles and populate unique_emails
        print("\n📊 Step 2: Migrating profiles...")
        await migrate_profiles(db)
        
        print("\n✅ Migration completed successfully!")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


async def migrate_companies(db):
    """Migrate companies and populate unique_domains collection"""
    shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
    
    total_companies = 0
    migrated_companies = 0
    skipped_companies = 0
    
    # Clear unique_domains collection
    await db.unique_domains.delete_many({})
    print("   Cleared unique_domains collection")
    
    domain_map = {}  # Track domains to handle duplicates
    
    for shard in shards:
        collection_name = f'companies_{shard}'
        companies = await db[collection_name].find({}).to_list(length=None)
        
        for company in companies:
            total_companies += 1
            
            # Check if company has a domain
            domain = company.get('domain', '').strip().lower() if company.get('domain') else None
            
            if not domain:
                # Generate domain from company name if missing
                company_name = company.get('name', '').lower().replace(' ', '').replace(',', '')
                domain = f"{company_name[:20]}.com" if company_name else f"company{company.get('id', 'unknown')}.com"
                
                # Update company with generated domain
                await db[collection_name].update_one(
                    {"id": company['id']},
                    {"$set": {"domain": domain}}
                )
                print(f"   Generated domain for company: {company.get('name')} -> {domain}")
            
            # Check for duplicate domains
            if domain in domain_map:
                skipped_companies += 1
                print(f"   ⚠️  Duplicate domain '{domain}' for company '{company.get('name')}' - using existing company")
                continue
            
            # Register domain in unique_domains
            try:
                await db.unique_domains.insert_one({
                    "id": str(uuid.uuid4()),
                    "domain": domain,
                    "company_id": company['id'],
                    "shard_name": collection_name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                domain_map[domain] = company['id']
                migrated_companies += 1
                
            except Exception as e:
                print(f"   ⚠️  Error registering domain '{domain}': {e}")
                skipped_companies += 1
    
    print(f"   ✅ Total companies: {total_companies}")
    print(f"   ✅ Migrated companies: {migrated_companies}")
    print(f"   ⚠️  Skipped (duplicates): {skipped_companies}")


async def migrate_profiles(db):
    """Migrate profiles to link them to companies and populate unique_emails"""
    shards = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['other']
    
    total_profiles = 0
    migrated_profiles = 0
    skipped_profiles = 0
    
    # Clear unique_emails collection
    await db.unique_emails.delete_many({})
    print("   Cleared unique_emails collection")
    
    # Build domain to company_id map
    domain_to_company_id = {}
    unique_domains = await db.unique_domains.find({}).to_list(length=None)
    for ud in unique_domains:
        domain_to_company_id[ud['domain']] = ud['company_id']
    
    print(f"   Loaded {len(domain_to_company_id)} company domains")
    
    email_set = set()  # Track emails to handle duplicates
    
    for shard in shards:
        collection_name = f'profiles_{shard}'
        profiles = await db[collection_name].find({}).to_list(length=None)
        
        for profile in profiles:
            total_profiles += 1
            
            # Get company domain
            company_domain = profile.get('company_domain', '').strip().lower() if profile.get('company_domain') else None
            
            if not company_domain:
                # Generate domain from company name if missing
                company_name = profile.get('company_name', '').lower().replace(' ', '').replace(',', '')
                company_domain = f"{company_name[:20]}.com" if company_name else f"company{total_profiles}.com"
            
            # Find company_id by domain
            company_id = domain_to_company_id.get(company_domain)
            
            if not company_id:
                print(f"   ⚠️  No company found for domain '{company_domain}' (profile: {profile.get('first_name')} {profile.get('last_name')})")
                skipped_profiles += 1
                continue
            
            # Update profile with company_id
            await db[collection_name].update_one(
                {"id": profile['id']},
                {"$set": {
                    "company_id": company_id,
                    "company_domain": company_domain
                }}
            )
            
            # Register emails in unique_emails
            emails = profile.get('emails', [])
            if emails:
                for email in emails:
                    email_normalized = email.lower().strip()
                    
                    # Skip duplicate emails
                    if email_normalized in email_set:
                        print(f"   ⚠️  Duplicate email '{email_normalized}' - skipping")
                        continue
                    
                    try:
                        await db.unique_emails.insert_one({
                            "id": str(uuid.uuid4()),
                            "email": email_normalized,
                            "profile_id": profile['id'],
                            "shard_name": collection_name,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        email_set.add(email_normalized)
                        
                    except Exception as e:
                        print(f"   ⚠️  Error registering email '{email_normalized}': {e}")
            
            migrated_profiles += 1
    
    print(f"   ✅ Total profiles: {total_profiles}")
    print(f"   ✅ Migrated profiles: {migrated_profiles}")
    print(f"   ✅ Registered emails: {len(email_set)}")
    print(f"   ⚠️  Skipped profiles: {skipped_profiles}")


if __name__ == "__main__":
    asyncio.run(migrate())
