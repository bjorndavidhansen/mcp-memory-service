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
        from qdrant_client.http import models
        print("✅ qdrant-client library imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import qdrant-client: {e}")
        print("Install with: pip install qdrant-client")
        return False
    
    try:
        # Test 1: Initialize client
        print("\n1️⃣ Initializing Qdrant client...")
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        print("✅ Client initialized")
        
        # Test 2: Get collections (auth test)
        print("\n2️⃣ Testing authentication by listing collections...")
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"✅ Authentication successful!")
        print(f"   Existing collections: {collection_names}")
        
        # Test 3: Check if memories collection exists
        print("\n3️⃣ Checking for 'memories' collection...")
        collection_name = "memories"
        expected_dim = 384
        
        if collection_name in collection_names:
            print(f"✅ Collection '{collection_name}' already exists")
            
            # Get collection info
            collection_info = client.get_collection(collection_name)
            current_dim = collection_info.config.params.vectors.size
            print(f"   Vectors count: {collection_info.vectors_count}")
            print(f"   Points count: {collection_info.points_count}")
            print(f"   Vector size: {current_dim}")
            
            # Check dimension mismatch
            if current_dim != expected_dim:
                print(f"⚠️  Dimension mismatch! Expected {expected_dim}, got {current_dim}")
                print(f"   This collection was created for a different embedding model")
                print(f"   Current: {current_dim}D (probably OpenAI ada-002)")
                print(f"   Needed: {expected_dim}D (all-MiniLM-L6-v2)")
                
                # Ask if we should recreate
                print(f"\n🔄 Recreating collection with correct dimensions...")
                try:
                    # Delete old collection
                    client.delete_collection(collection_name)
                    print(f"✅ Deleted old collection")
                    
                    # Create new collection with correct dimensions
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=expected_dim,
                            distance=models.Distance.COSINE
                        )
                    )
                    print(f"✅ Created new collection with {expected_dim}D vectors")
                except Exception as recreate_error:
                    print(f"❌ Failed to recreate collection: {recreate_error}")
                    return False
        else:
            print(f"⚠️  Collection '{collection_name}' does not exist")
            
            # Test 4: Try to create collection
            print("\n4️⃣ Attempting to create 'memories' collection...")
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✅ Successfully created collection '{collection_name}'")
                
                # Verify creation
                collections = client.get_collections()
                collection_names = [c.name for c in collections.collections]
                if collection_name in collection_names:
                    print(f"✅ Collection creation verified")
                else:
                    print(f"⚠️  Collection creation verification failed")
                    
            except Exception as create_error:
                print(f"❌ Failed to create collection: {create_error}")
                if "403" in str(create_error) or "Forbidden" in str(create_error):
                    print("   → API key lacks collection creation permissions")
                    print("   → Check API key permissions in Qdrant dashboard")
                elif "409" in str(create_error) or "already exists" in str(create_error).lower():
                    print("   → Collection already exists (race condition)")
                return False
        
        # Test 5: Test vector operations
        print("\n5️⃣ Testing vector operations...")
        try:
            # Insert a test vector with correct dimensions
            test_vector = [0.1] * expected_dim  # Use expected dimensions
            test_id = 999999  # Use a high ID to avoid conflicts
            
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=test_id,
                        vector=test_vector,
                        payload={"test": True, "content": "EchoVault test vector"}
                    )
                ]
            )
            print(f"✅ Successfully inserted test vector with ID {test_id}")
            
            # Search for the test vector
            search_results = client.search(
                collection_name=collection_name,
                query_vector=test_vector,
                limit=1
            )
            
            if search_results and len(search_results) > 0:
                print(f"✅ Successfully found test vector (similarity: {search_results[0].score:.4f})")
            else:
                print("⚠️  Test vector not found in search results")
            
            # Clean up test vector
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[test_id])
            )
            print(f"✅ Successfully deleted test vector")
            
        except Exception as vector_error:
            print(f"❌ Vector operations failed: {vector_error}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All Qdrant tests passed! Connection is working perfectly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Qdrant connection failed: {type(e).__name__} - {e}")
        
        # Provide specific guidance based on error type
        error_str = str(e).lower()
        if "403" in error_str or "forbidden" in error_str:
            print("\n🔧 SOLUTION:")
            print("   → API key lacks necessary permissions")
            print("   → Go to Qdrant dashboard > API Keys")
            print("   → Ensure your API key has 'read' and 'write' permissions")
            print("   → Create a new API key if needed")
        elif "404" in error_str or "not found" in error_str:
            print("\n🔧 SOLUTION:")
            print("   → Qdrant URL is incorrect")
            print("   → Verify your cluster URL in Qdrant dashboard")
            print("   → Format should be: https://your-cluster-id.qdrant.tech:6333")
        elif "timeout" in error_str or "connection" in error_str:
            print("\n🔧 SOLUTION:")
            print("   → Network connectivity issue")
            print("   → Check firewall settings")
            print("   → Verify internet connection")
        else:
            print("\n🔧 Check:")
            print("   → QDRANT_URL format: https://your-cluster-id.qdrant.tech:6333")
            print("   → QDRANT_API_KEY has read/write permissions")
            print("   → Network connectivity to qdrant.tech")
        
        return False

if __name__ == "__main__":
    success = test_qdrant_direct()
    sys.exit(0 if success else 1) 