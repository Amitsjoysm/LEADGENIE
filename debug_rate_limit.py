#!/usr/bin/env python3
"""
Debug Rate Limiting Configuration
"""

import asyncio
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address

async def test_slowapi_directly():
    """Test slowapi configuration directly"""
    print("🔍 Testing SlowAPI Configuration")
    print("=" * 50)
    
    # Test Redis connection
    redis_url = "redis://localhost:6379/0"
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Test Limiter creation
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=redis_url
        )
        print("✅ Limiter created successfully")
        print(f"Storage URI: {limiter.storage_uri}")
        print(f"Key function: {limiter.key_func}")
    except Exception as e:
        print(f"❌ Limiter creation failed: {e}")
        return
    
    # Check if Redis keys are being created
    try:
        # Clear any existing keys
        keys = r.keys("LIMITER*")
        if keys:
            r.delete(*keys)
            print(f"Cleared {len(keys)} existing limiter keys")
        
        print("✅ Rate limiter setup appears correct")
        
        # Check current Redis keys
        all_keys = r.keys("*")
        print(f"Current Redis keys: {len(all_keys)}")
        for key in all_keys[:10]:  # Show first 10 keys
            print(f"  {key}")
            
    except Exception as e:
        print(f"❌ Redis key check failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_slowapi_directly())