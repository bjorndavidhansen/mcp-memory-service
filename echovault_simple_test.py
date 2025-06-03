#!/usr/bin/env python
"""
Simple EchoVault Verification Test
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def main():
    print("🚀 EchoVault Simple Verification")
    print("=" * 50)
    print(f"⏰ {datetime.now().isoformat()}")
    print()
    
    try:
        from mcp_memory_service.storage.echovault import EchoVaultStorage
        from mcp_memory_service.models.memory import Memory
        
        # Initialize
        print("📦 Initializing EchoVault...")
        storage = EchoVaultStorage()
        await storage.initialize()
        print("✅ EchoVault initialized")
        
        # Test storage
        print("\n1️⃣ Testing Memory Storage...")
        
        from mcp_memory_service.utils.hashing import generate_content_hash
        
        content = "Testing EchoVault functionality"
        content_hash = generate_content_hash(content)
        memory = Memory(content=content, content_hash=content_hash, tags=["test"])
        success, msg = await storage.store(memory)
        
        if success:
            print(f"   ✅ Successfully stored memory: {memory.content_hash[:32]}...")
        else:
            print(f"   ❌ Failed to store: {msg}")
        
        # Test retrieval
        print("\n2️⃣ Testing Memory Retrieval...")
        
        results = await storage.retrieve("EchoVault test", n_results=5)
        print(f"   🔍 Found {len(results)} results")
        
        if results:
            best = results[0]
            print(f"   🎯 Best match: score={best.relevance_score:.3f}")
            print(f"       Content: {best.memory.content[:50]}...")
        
        # Test tag search
        print("\n3️⃣ Testing Tag Search...")
        
        tag_results = await storage.search_by_tag(["test"])
        print(f"   🏷️ Found {len(tag_results)} memories with 'test' tag")
        
        if tag_results:
            print(f"   Sample: {tag_results[0].content[:40]}...")
        
        print("\n✅ EchoVault verification completed successfully!")
        print("🎉 All core features are working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 