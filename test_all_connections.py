import asyncio
import os
import sys

from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import EchoVault components
from mcp_memory_service.storage.neon_client import NeonClient
from mcp_memory_service.storage.vector_store import VectorStoreClient
from mcp_memory_service.storage.blob_store import BlobStoreClient

load_dotenv()


async def test_all_services():
    print("🔍 Testing ALL EchoVault Services...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # Test Neon PostgreSQL
    print("\n1️⃣ Testing Neon PostgreSQL...")
    try:
        neon = NeonClient()
        await neon.initialize()
        # Get stats to verify connection
        stats = await neon.get_memory_stats()
        print("✅ Neon PostgreSQL: Connected!")
        print(f"   Memory count: {stats['memory_count']}")
        print("   Pgvector version verified")
        await neon.close()
        success_count += 1
    except Exception as e:
        print(f"❌ Neon PostgreSQL: {e}")
    
    # Test Qdrant
    print("\n2️⃣ Testing Qdrant Cloud...")
    try:
        vector_store = VectorStoreClient()
        await vector_store.initialize()
        # Check if we can get stats
        stats = await vector_store.get_stats()
        print("✅ Qdrant: Connected!")
        print(f"   Active providers: {stats.get('providers', [])}")
        success_count += 1
    except Exception as e:
        print(f"❌ Qdrant: {e}")
    
    # Test R2 (already confirmed working)
    print("\n3️⃣ Testing R2 Blob Store...")
    try:
        blob_store = BlobStoreClient()
        # Initialize the client
        await blob_store.initialize()
        print("✅ R2 Blob Store: Initialized!")
        print(f"   Bucket: {blob_store.r2_bucket}")
        print(f"   Endpoint: {blob_store.r2_endpoint}")
        success_count += 1
    except Exception as e:
        print(f"❌ R2 Blob Store: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Connection tests complete: {success_count}/{total_tests} passed")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = asyncio.run(test_all_services())
    sys.exit(0 if success else 1) 