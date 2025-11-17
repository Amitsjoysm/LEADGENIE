"""
Seed data script for LeadGen Pro
Creates test data for users, plans, profiles, and companies
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import config
from utils import hash_password
from datetime import datetime, timezone
import uuid
import random

# Sample data
INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Manufacturing", "Retail",
    "Real Estate", "Education", "Consulting", "Marketing", "Legal"
]

SUB_INDUSTRIES = {
    "Technology": ["Software", "Hardware", "Cloud Services", "Cybersecurity", "AI/ML"],
    "Healthcare": ["Pharmaceuticals", "Medical Devices", "Hospitals", "Telemedicine"],
    "Finance": ["Banking", "Insurance", "Investment", "Fintech"],
    "Manufacturing": ["Automotive", "Electronics", "Food & Beverage", "Chemicals"],
    "Retail": ["E-commerce", "Fashion", "Grocery", "Electronics"]
}

JOB_TITLES = [
    "CEO", "CTO", "CFO", "VP Sales", "VP Marketing",
    "Sales Director", "Marketing Manager", "Business Development Manager",
    "Account Executive", "Sales Representative", "Product Manager",
    "Engineering Manager", "HR Director", "Operations Manager"
]

FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
    "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Charles",
    "Linda", "Joseph", "Elizabeth", "Thomas", "Susan", "Christopher", "Jessica",
    "Daniel", "Karen", "Matthew", "Nancy", "Anthony", "Betty", "Mark", "Helen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Thompson", "White", "Harris", "Clark", "Lewis", "Robinson", "Walker"
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Boston", "Detroit", "Portland", "Memphis", "Atlanta"
]

STATES = {
    "New York": "NY", "Los Angeles": "CA", "Chicago": "IL", "Houston": "TX",
    "Phoenix": "AZ", "Philadelphia": "PA", "San Antonio": "TX", "San Diego": "CA",
    "Dallas": "TX", "San Jose": "CA", "Austin": "TX", "Jacksonville": "FL",
    "Seattle": "WA", "Denver": "CO", "Boston": "MA", "Detroit": "MI",
    "Portland": "OR", "Memphis": "TN", "Atlanta": "GA"
}

COMPANY_NAMES = [
    "Acme Corp", "TechVision", "GlobalSoft", "InnovateLabs", "DataDrive",
    "CloudFirst", "SecureNet", "SmartSolutions", "NextGen Systems", "FutureWorks",
    "Digital Dynamics", "Quantum Technologies", "Synergy Inc", "Pinnacle Group",
    "Vertex Solutions", "Catalyst Ventures", "Momentum Digital", "Apex Systems"
]

EMPLOYEE_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
REVENUE_RANGES = ["$0-1M", "$1M-10M", "$10M-50M", "$50M-100M", "$100M-500M", "$500M+"]


def get_shard_key(name: str) -> str:
    """Get shard suffix based on first letter of name"""
    if not name:
        return 'other'
    first_letter = name[0].lower()
    if first_letter.isalpha():
        return first_letter
    return 'other'


async def create_seed_data():
    """Create comprehensive seed data"""
    print("="*60)
    print("Starting seed data generation...")
    print("="*60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    try:
        # 1. Create Super Admin User
        print("\n1. Creating Super Admin user...")
        admin_password = hash_password("admin123")
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@leadgen.com",
            "password": admin_password,
            "full_name": "Admin User",
            "role": "super_admin",
            "credits": 1000,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.delete_one({"email": "admin@leadgen.com"})
        await db.users.insert_one(admin_user)
        print("   ✓ Super Admin: admin@leadgen.com / admin123")
        
        # 2. Create Regular Test Users
        print("\n2. Creating test users...")
        test_users = []
        for i in range(5):
            user_password = hash_password("password123")
            user = {
                "id": str(uuid.uuid4()),
                "email": f"user{i+1}@example.com",
                "password": user_password,
                "full_name": f"Test User {i+1}",
                "role": "user",
                "credits": 50 + (i * 10),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            test_users.append(user)
            await db.users.delete_one({"email": user['email']})
            await db.users.insert_one(user)
        print(f"   ✓ Created {len(test_users)} test users (user1@example.com - user5@example.com)")
        print("   Password for all: password123")
        
        # 3. Create Plans
        print("\n3. Creating subscription plans...")
        plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "Starter",
                "credits": 100,
                "price": 29.99,
                "duration_days": 30,
                "features": ["100 credits", "Email reveals", "Basic support"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Professional",
                "credits": 500,
                "price": 99.99,
                "duration_days": 30,
                "features": ["500 credits", "Email + Phone reveals", "Priority support", "Export data"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Enterprise",
                "credits": 2000,
                "price": 299.99,
                "duration_days": 30,
                "features": ["2000 credits", "All contact reveals", "Dedicated support", "API access", "Custom integrations"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.plans.delete_many({})
        await db.plans.insert_many(plans)
        print(f"   ✓ Created {len(plans)} subscription plans")
        
        # 4. Create Companies with unique domains
        print("\n4. Creating companies (this may take a moment)...")
        companies_created = 0
        company_map = {}  # domain -> company_id mapping
        
        # Clear unique_domains collection
        await db.unique_domains.delete_many({})
        
        for i in range(1000):  # Create 1000 companies
            city = random.choice(CITIES)
            industry = random.choice(INDUSTRIES)
            company_id = str(uuid.uuid4())
            domain = f"company{i+1}.com"
            
            company = {
                "id": company_id,
                "name": f"{random.choice(COMPANY_NAMES)} {i+1}",
                "domain": domain,
                "linkedin_url": f"https://linkedin.com/company/company{i+1}",
                "revenue": random.choice(REVENUE_RANGES),
                "employee_size": random.choice(EMPLOYEE_SIZES),
                "industry": industry,
                "description": f"Leading {industry.lower()} company providing innovative solutions",
                "city": city,
                "state": STATES.get(city, "CA"),
                "country": "USA",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            shard = get_shard_key(company['name'])
            collection_name = f'companies_{shard}'
            await db[collection_name].insert_one(company)
            
            # Register domain in unique_domains collection
            await db.unique_domains.insert_one({
                "id": str(uuid.uuid4()),
                "domain": domain,
                "company_id": company_id,
                "shard_name": collection_name,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            company_map[domain] = company_id
            companies_created += 1
            
            if (i + 1) % 200 == 0:
                print(f"   Progress: {i+1}/1000 companies created...")
        
        print(f"   ✓ Created {companies_created} companies across sharded collections")
        print(f"   ✓ Registered {len(company_map)} unique domains")
        
        # 5. Create Profiles with company relationships and unique emails
        print("\n5. Creating profiles (this may take a few moments)...")
        profiles_created = 0
        emails_registered = 0
        
        # Clear unique_emails collection
        await db.unique_emails.delete_many({})
        
        for i in range(5000):  # Create 5000 profiles
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            industry = random.choice(INDUSTRIES)
            sub_industry = random.choice(SUB_INDUSTRIES.get(industry, ["Other"]))
            city = random.choice(CITIES)
            
            # Link to existing company
            company_domain = f"company{random.randint(1, 1000)}.com"
            company_id = company_map.get(company_domain, company_map[f"company{random.randint(1, 100)}.com"])  # Fallback
            company_name = f"{random.choice(COMPANY_NAMES)} {company_domain.replace('.com', '').replace('company', '')}"
            
            profile_id = str(uuid.uuid4())
            email = f"{first_name.lower()}.{last_name.lower()}{i}@{company_domain}"
            
            profile = {
                "id": profile_id,
                "first_name": first_name,
                "last_name": last_name,
                "job_title": random.choice(JOB_TITLES),
                "industry": industry,
                "sub_industry": sub_industry,
                "keywords": [industry, sub_industry, random.choice(JOB_TITLES)],
                "seo_description": f"{first_name} {last_name} - {random.choice(JOB_TITLES)} at {company_name}",
                "company_id": company_id,  # NEW: Link to company
                "company_name": company_name,
                "company_domain": company_domain,
                "profile_linkedin_url": f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}{i}",
                "company_linkedin_url": f"https://linkedin.com/company/{company_name.lower().replace(' ', '')}",
                "emails": [email],
                "phones": [f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"],
                "city": city,
                "state": STATES.get(city, "CA"),
                "country": "USA",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            shard = get_shard_key(last_name)
            collection_name = f'profiles_{shard}'
            await db[collection_name].insert_one(profile)
            profiles_created += 1
            
            # Register email in unique_emails collection
            await db.unique_emails.insert_one({
                "id": str(uuid.uuid4()),
                "email": email.lower(),
                "profile_id": profile_id,
                "shard_name": collection_name,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            emails_registered += 1
            
            if (i + 1) % 1000 == 0:
                print(f"   Progress: {i+1}/5000 profiles created...")
        
        print(f"   ✓ Created {profiles_created} profiles across sharded collections")
        print(f"   ✓ Registered {emails_registered} unique emails")
        
        print("\n" + "="*60)
        print("SEED DATA GENERATION COMPLETE!")
        print("="*60)
        print("\nCredentials:")
        print("  Super Admin: admin@leadgen.com / admin123")
        print("  Test Users: user1@example.com - user5@example.com / password123")
        print("\nDatabase Summary:")
        print(f"  • Users: {len(test_users) + 1}")
        print(f"  • Plans: {len(plans)}")
        print(f"  • Companies: {companies_created}")
        print(f"  • Profiles: {profiles_created}")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during seed data generation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_seed_data())
