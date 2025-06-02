#!/usr/bin/env python
"""
Direct Qdrant Connection Test
Tests Qdrant Cloud connectivity without EchoVault wrapper
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_qdrant_direct():
    print("🔍 Testing Qdrant Cloud Direct Connection...")
    print("=" * 50)
    
    # Get credentials from environment
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    print(f"QDRANT_URL: {qdrant_url}")
    print(f"QDRANT_API_KEY: {'*' * (len(qdrant_api_key) - 4) + qdrant_api_key[-4:] if qdrant_api_key else 'NOT SET'}")
    
    if not qdrant_url or not qdrant_api_key:
        print("❌ Qdrant credentials not found in environment")
        return False
    
    try:
        from qdrant_client import QdrantClient
        print("✅ qdrant_client imported successfully")
        
        # Test 1: Basic client creation
        print("\n1️⃣ Creating Qdrant client...")
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        print("✅ Client created successfully")
        
        # Test 2: Get server info
        print("\n2️⃣ Getting server info...")
        try:
            info = client.get_collections()
            print(f"✅ Server responding! Collections: {len(info.collections)}")
            for collection in info.collections:
                print(f"   - {collection.name}")
        except Exception as e:
            print(f"❌ Failed to get collections: {e}")
            # Try simpler operation
            print("\n🔄 Trying basic health check...")
            try:
                # Try to get cluster info instead
                cluster_info = client.http.cluster.cluster_status()
                print(f"✅ Basic connectivity works! Cluster status available")
                return True
            except Exception as e2:
                print(f"❌ Basic connectivity failed: {e2}")
                return False
        
        # Test 3: Try to create a test collection
        print("\n3️⃣ Testing collection operations...")
        test_collection = "echovault_test"
        try:
            # Check if collection exists
            collections = client.get_collections()
            existing_names = [c.name for c in collections.collections]
            
            if test_collection in existing_names:
                print(f"✅ Test collection '{test_collection}' already exists")
            else:
                print(f"⚠️  Test collection '{test_collection}' doesn't exist")
                # We won't try to create it automatically to avoid permissions issues
        
            return True
            
        except Exception as e:
            print(f"❌ Collection operations failed: {e}")
            return False
    
    except ImportError:
        print("❌ qdrant-client not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qdrant_direct()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Qdrant connection test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Qdrant connection test failed")
        sys.exit(1) 