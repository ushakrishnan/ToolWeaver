# Phase 7 Free Tier Cloud Options - Quick Reference

## ✅ YES, Both Free Tiers Are Feasible!

### Qdrant Cloud Free Tier
- **Storage**: 1 GB
- **Vectors**: 100,000
- **Tools**: ~2,600 (with 384-dim embeddings)
- **Availability**: Always-on
- **Cost**: $0/month forever
- **Setup**: 5 minutes at https://cloud.qdrant.io
- **Credit Card**: NOT required
- **Perfect For**: Development, testing, small production (up to 2,600 tools)

### Redis Cloud Free Tier
- **Memory**: 30 MB
- **Connections**: 30 concurrent
- **Capacity**: ~5,000 tool entries, ~30,000 search caches
- **Availability**: Always-on
- **Cost**: $0/month forever
- **Setup**: 5 minutes at https://redis.io/cloud
- **Credit Card**: NOT required
- **Perfect For**: Development, testing, proof of concepts

---

## Environment Setup (.env)

```bash
# ============================================================
# QDRANT VECTOR DATABASE - Choose ONE option
# ============================================================

# Option 1: Local Docker (FREE, unlimited storage)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Option 2: Qdrant Cloud Free (FREE, 1 GB, 100k vectors) ⭐ RECOMMENDED
# QDRANT_URL=https://xxxxx.us-east-1-0.aws.cloud.qdrant.io
# QDRANT_API_KEY=your-qdrant-cloud-api-key

# Option 3: Azure Container Instances (PAID, ~$30/month)
# QDRANT_URL=http://toolweaver-qdrant.eastus.azurecontainer.io:6333

# ============================================================
# REDIS DISTRIBUTED CACHE - Choose ONE option
# ============================================================

# Option 1: Local Docker (FREE, unlimited memory)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Option 2: Redis Cloud Free (FREE, 30 MB) ⭐ RECOMMENDED
# REDIS_URL=redis://redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345
# REDIS_PASSWORD=your-redis-cloud-password

# Option 3: Azure Cache for Redis (PAID, $18-266/month)
# REDIS_URL=rediss://toolweaver-cache.redis.cache.windows.net:6380
# REDIS_PASSWORD=your-azure-redis-primary-key

# Enable fallback to file cache
REDIS_FALLBACK_ENABLED=true
```

---

## Quick Setup Guide

### Qdrant Cloud (10 minutes)

1. **Sign Up**: https://cloud.qdrant.io (no credit card)
2. **Create Cluster**: 
   - Name: `toolweaver-dev`
   - Region: Nearest (e.g., us-east-1)
   - Plan: **Free** (1 GB)
3. **Get Credentials**:
   - Copy cluster URL: `https://xxxxx.us-east-1-0.aws.cloud.qdrant.io`
   - Generate API key (save it!)
4. **Create Collection** (in Qdrant Cloud dashboard):
   ```
   Collection Name:     toolweaver_tools
   Use Case:           Global search
   Search Type:        Simple Hybrid Search
   
   Dense Vector:
     Name:             default
     Dimensions:       384
     Metric:           Cosine
   
   Sparse Vector:
     Name:             sparse (or bm25)
     Use IDF:          No (unchecked)
   ```
   *Note: Sparse vector is required by UI but not used by ToolWeaver*
5. **Update .env**:
   ```bash
   QDRANT_URL=https://xxxxx.us-east-1-0.aws.cloud.qdrant.io
   QDRANT_API_KEY=your-key-here
   QDRANT_COLLECTION=toolweaver_tools
   ```

### Redis Cloud (5 minutes)

1. **Sign Up**: https://redis.io/cloud (no credit card)
2. **Create Database**:
   - Name: `toolweaver-cache`
   - Region: Nearest (e.g., us-east-1)
   - Plan: **Free** (30 MB)
3. **Get Credentials**:
   - Copy endpoint: `redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345`
   - Copy password (click "View")
4. **Update .env**:
   ```bash
   REDIS_URL=redis://redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345
   REDIS_PASSWORD=your-password-here
   ```

---

## Testing Your Setup

```powershell
# Quick test both services
python scripts/test_cloud_connections.py

# Or test individually:
# Activate venv
cd C:\Usha\UKRepos\ToolWeaver
.\.venv\Scripts\Activate.ps1

# Test Qdrant
python -c "
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)
print('Qdrant:', client.get_collections())
"

# Test Redis
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('REDIS_URL')
host = url.split('//')[1].split(':')[0]
port = int(url.split(':')[-1])

client = redis.Redis(
    host=host,
    port=port,
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)
print('Redis ping:', client.ping())
"
```

---

## Capacity Planning

### Qdrant Free Tier (1 GB)

**What fits?**
- 384-dim embeddings: ~100,000 vectors
- ToolWeaver tools: ~2,600 tools (with metadata)
- Calculation: 384 dims × 4 bytes + metadata ≈ 400 KB per 1000 vectors

**When to upgrade?**
- You need more than 2,600 tools
- Upgrade to 5 GB ($25/month) = ~13,000 tools

### Redis Free Tier (30 MB)

**What fits?**
- Tool catalog cache: ~5,000 entries (6 KB each)
- Search results: ~30,000 cached queries (1 KB each)
- Embeddings: ~75,000 cached embeddings (400 bytes each)

**Optimization for 30 MB**:
```python
# Adjust TTLs for smaller cache
tool_cache.CATALOG_TTL = 6 * 3600   # 6h instead of 24h
tool_cache.SEARCH_TTL = 30 * 60     # 30m instead of 1h
tool_cache.EMBEDDING_TTL = 24 * 3600  # 24h instead of 7d
```

**When to upgrade?**
- Cache evictions happening too frequently
- Upgrade to 100 MB ($7/month) for 3x capacity

---

## Requirements.txt

Already added in your project:

```pip
# Phase 7: Scale Optimization (1000+ tools)
qdrant-client>=1.16.0  # Vector database
redis>=5.0.0  # Distributed caching
```

Install both:
```powershell
pip install qdrant-client redis
```

---

## Complete Deployment Options

| Option | Qdrant | Redis | Total Cost | Best For |
|--------|--------|-------|------------|----------|
| **All Local** | Docker | Docker | $0 | Development |
| **Free Cloud** | Cloud Free | Cloud Free | $0 | Dev/Testing/Small Prod |
| **Hybrid** | Cloud Free | Local | $0 | Testing scaled search |
| **Azure Budget** | ACI | Basic C0 | $48/mo | Small production |
| **Azure Production** | ACI | Standard C1 | $75/mo | Production |

---

## Monitoring

### Qdrant Cloud Dashboard
- https://cloud.qdrant.io
- View: Storage used, vectors indexed, queries/sec
- Alerts: Email when approaching 1 GB limit

### Redis Cloud Dashboard
- https://app.redislabs.com
- View: Memory usage, operations/sec, latency
- Alerts: Email when memory >80%

---

## Automatic Fallback

ToolWeaver automatically handles failures:

```python
# Qdrant unavailable? → Uses in-memory search
search_engine = VectorToolSearchEngine(
    qdrant_url=os.getenv("QDRANT_URL"),
    fallback_to_memory=True  # ✅ Always enabled
)

# Redis unavailable? → Uses file cache
redis_cache = RedisCache(
    redis_url=os.getenv("REDIS_URL"),
    enable_fallback=True  # ✅ Always enabled
)
```

**No code changes needed when switching between local/cloud!**

---

## Recommendation

### For Your Project (ToolWeaver Development)

**Best Setup**: Free Cloud Tier for Both

1. **Qdrant Cloud Free** (not local Docker)
   - ✅ Always available (even when laptop off)
   - ✅ No local resource usage
   - ✅ 99.99% uptime
   - ✅ 1 GB = plenty for development
   - ✅ Easy to share with team

2. **Redis Cloud Free** (not local Docker)
   - ✅ Always available
   - ✅ No local resource usage
   - ✅ 30 MB = sufficient for cache layer
   - ✅ Easy monitoring dashboard

**Why not local?**
- Docker uses memory/CPU on your machine
- Must remember to start containers
- Data only available when laptop on
- No monitoring dashboards

**Setup time**: 10 minutes total for both

---

## Next Steps

1. ✅ Sign up for Qdrant Cloud (free)
2. ✅ Sign up for Redis Cloud (free)
3. ✅ Update `.env` with credentials
4. ✅ Run tests: `pytest tests/test_vector_search.py tests/test_redis_cache.py -v`
5. ✅ Deploy and monitor usage

Both free tiers are 100% feasible and recommended for ToolWeaver development!
