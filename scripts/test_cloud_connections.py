"""Test Qdrant and Redis Cloud connections"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_qdrant():
    """Test Qdrant Cloud connection"""
    print("=" * 60)
    print("TESTING QDRANT CLOUD CONNECTION")
    print("=" * 60)
    
    try:
        from qdrant_client import QdrantClient
        
        url = os.getenv('QDRANT_URL')
        api_key = os.getenv('QDRANT_API_KEY')
        collection_name = os.getenv('QDRANT_COLLECTION', 'toolweaver_tools')
        
        print(f"\n📍 URL: {url}")
        print(f"🔑 API Key: {'*' * 20}{api_key[-10:] if api_key else 'None'}")
        print(f"📦 Collection: {collection_name}")
        print("\nConnecting...")
        
        client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=10
        )
        
        # Test 1: List collections
        collections = client.get_collections()
        print(f"\n✅ Connected successfully!")
        print(f"📚 Existing collections: {[c.name for c in collections.collections]}")
        
        # Test 2: Check our collection
        try:
            info = client.get_collection(collection_name)
            print(f"\n✅ Collection '{collection_name}' exists:")
            print(f"   📊 Vectors: {info.points_count}")
            print(f"   🔢 Dimensions: {info.config.params.vectors.size if info.config.params.vectors else 'N/A'}")
            print(f"   📈 Status: {info.status}")
        except Exception as e:
            print(f"\nℹ️  Collection '{collection_name}' not found")
            print("   (Will be created automatically on first use)")
        
        print("\n🎉 Qdrant Cloud is READY!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   {str(e)}\n")
        return False


def test_redis():
    """Test Redis Cloud connection"""
    print("=" * 60)
    print("TESTING REDIS CLOUD CONNECTION")
    print("=" * 60)
    
    try:
        import redis
        
        redis_url = os.getenv('REDIS_URL')
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # Parse URL
        if redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', '')
        
        if ':' in redis_url:
            host, port = redis_url.rsplit(':', 1)
            port = int(port)
        else:
            host = redis_url
            port = 6379
        
        print(f"\n📍 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🔑 Password: {'*' * 20}{redis_password[-10:] if redis_password else 'None'}")
        print("\nConnecting...")
        
        client = redis.Redis(
            host=host,
            port=port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=10
        )
        
        # Test 1: Ping
        pong = client.ping()
        print(f"\n✅ Connected successfully! (PING: {pong})")
        
        # Test 2: Get info
        info = client.info('server')
        print(f"📊 Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"🖥️  OS: {info.get('os', 'Unknown')}")
        
        # Test 3: Memory info
        memory = client.info('memory')
        used_memory = memory.get('used_memory_human', 'Unknown')
        max_memory = memory.get('maxmemory_human', 'Unknown')
        print(f"💾 Memory used: {used_memory}")
        if max_memory and max_memory != '0B':
            print(f"💾 Memory limit: {max_memory}")
        
        # Test 4: Set/Get test
        test_key = 'toolweaver:test'
        test_value = 'Hello from ToolWeaver!'
        
        client.set(test_key, test_value, ex=60)  # 60 second TTL
        retrieved = client.get(test_key)
        
        if retrieved == test_value:
            print(f"\n✅ Read/Write test passed!")
            print(f"   Set: '{test_value}'")
            print(f"   Get: '{retrieved}'")
            client.delete(test_key)
        
        # Test 5: Check existing keys
        keys = client.keys('toolweaver:*')
        print(f"\n📦 Existing ToolWeaver keys: {len(keys)}")
        if keys:
            print(f"   Sample: {keys[:5]}")
        
        print("\n🎉 Redis Cloud is READY!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   {str(e)}\n")
        return False


if __name__ == "__main__":
    print("\n🚀 Testing Cloud Services\n")
    
    qdrant_ok = test_qdrant()
    redis_ok = test_redis()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Qdrant Cloud: {'✅ READY' if qdrant_ok else '❌ FAILED'}")
    print(f"Redis Cloud:  {'✅ READY' if redis_ok else '❌ FAILED'}")
    print()
    
    if qdrant_ok and redis_ok:
        print("🎉 All cloud services are operational!")
        print("You can now run: pytest tests/test_vector_search.py tests/test_redis_cache.py -v")
    else:
        print("⚠️  Some services failed. Check credentials in .env")
    
    print()
