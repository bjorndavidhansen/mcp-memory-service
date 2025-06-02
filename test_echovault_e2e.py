import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_memory_service.storage.echovault import EchoVaultStorage
from mcp_memory_service.models.memory import Memory
from mcp_memory_service.utils.hashing import generate_content_hash

load_dotenv()


async def test_echovault():
    print("🧪 Testing EchoVault End-to-End...")
    print("=" * 50)
    
    try:
        # Initialize EchoVault
        print("\n🔧 Initializing EchoVault...")
        storage = EchoVaultStorage("./test_chroma_path")
        
        # Test 1: Store a memory
        print("\n1️⃣ Storing test memory...")
        test_content = "Testing EchoVault with all services operational"
        metadata = {
            "tags": ["test", "echovault", "integration"],
            "type": "test_memory",
            "timestamp": datetime.now().isoformat()
        }
        
        # Create a Memory object
        content_hash = generate_content_hash(test_content, metadata)
        now = datetime.now().timestamp()
        memory = Memory(
            content=test_content,
            content_hash=content_hash,
            tags=["test", "echovault", "integration"],
            memory_type="test_memory",
            metadata=metadata,
            created_at=now,
            created_at_iso=datetime.utcfromtimestamp(now).isoformat() + "Z"
        )
        
        success, message = await storage.store(memory)
        print(f"✅ Store result: {message}")
        
        # Test 2: Retrieve memories
        print("\n2️⃣ Querying memories...")
        results = await storage.retrieve("EchoVault services", n_results=5)
        print(f"✅ Found {len(results)} results")
        
        for i, result in enumerate(results):
            content_preview = result.memory.content[:50]
            print(f"   Result {i+1}: Score={result.relevance_score:.3f}, Content={content_preview}...")
        
        # Test 3: Search by tags
        print("\n3️⃣ Searching by tags...")
        tag_results = await storage.search_by_tag(["test"])
        print(f"✅ Found {len(tag_results)} memories with 'test' tag")
        
        for i, memory in enumerate(tag_results):
            print(f"   Memory {i+1}: {memory.content[:50]}...")
        
        # Test 4: Get stats (if available)
        print("\n4️⃣ Getting storage stats...")
        if hasattr(storage, 'get_stats'):
            stats = await storage.get_stats()
            print("✅ Stats retrieved:")
            print(f"   Total memories: {stats.get('memory_count', 0)}")
            print(f"   Blob storage used: {stats.get('blob_count', 0)}")
            print("   Vector dimensions: " + str(stats.get('avg_vector_size', 'N/A')))
        else:
            print("⚠️  get_stats method not available on EchoVaultStorage")
        
        print("\n🎉 EchoVault is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ EchoVault test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_echovault())
    sys.exit(0 if success else 1) 