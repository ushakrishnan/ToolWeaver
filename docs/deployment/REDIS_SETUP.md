# Redis Setup Guide for ToolWeaver Phase 7

This guide covers setting up Redis for distributed caching with three deployment options.

---

## Option 1: Local Redis with Docker (Windows)

### Prerequisites
- Docker Desktop for Windows installed
- WSL 2 backend enabled

### Setup

1. **Start Redis with docker-compose**:
```powershell
cd C:\Usha\UKRepos\ToolWeaver
docker-compose up -d redis
```

2. **Verify Redis is running**:
```powershell
docker ps | Select-String redis
# Should show: toolweaver-redis running on port 6379
```

3. **Test connection**:
```powershell
docker exec -it toolweaver-redis redis-cli ping
# Should return: PONG
```

4. **Configure ToolWeaver**:
```bash
# .env file
REDIS_URL=redis://localhost:6379
```

### Stop Redis
```powershell
docker-compose stop redis
```

---

## Option 2: Local Redis with WSL 2

### Prerequisites
- WSL 2 installed (`wsl --install`)
- Ubuntu or Debian distribution

### Setup

1. **Install Redis in WSL**:
```bash
# Open WSL terminal
wsl

# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server -y
```

2. **Configure Redis**:
```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Change these settings:
# bind 127.0.0.1 ::1 to bind 0.0.0.0
# supervised no to supervised systemd
```

3. **Start Redis service**:
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server  # Auto-start on boot

# Check status
sudo systemctl status redis-server
```

4. **Test connection from WSL**:
```bash
redis-cli ping
# Should return: PONG
```

5. **Find WSL IP address**:
```bash
ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1
# Example output: 172.xx.xx.xx
```

6. **Configure ToolWeaver (from Windows)**:
```bash
# .env file
REDIS_URL=redis://172.xx.xx.xx:6379
# Replace with your WSL IP from step 5
```

### Access from Windows
```powershell
# Test from PowerShell (requires redis-cli for Windows)
redis-cli -h 172.xx.xx.xx -p 6379 ping
```

### Stop Redis
```bash
# In WSL
sudo systemctl stop redis-server
```

---

## Option 3: Azure Cache for Redis (Cloud)

### Prerequisites
- Azure subscription
- Azure CLI installed (`az login`)

### Setup via Azure Portal

1. **Create Redis Cache**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Click "Create a resource" → Search "Azure Cache for Redis"
   - Click "Create"

2. **Configure**:
   - **Name**: `toolweaver-cache` (must be globally unique)
   - **Resource Group**: Create new or select existing
   - **Location**: Choose nearest region (e.g., East US)
   - **Cache tier**:
     - **Basic C0** (250 MB): $0.024/hour - Development
     - **Standard C1** (1 GB): $0.061/hour - Testing
     - **Premium P1** (6 GB): $0.364/hour - Production with clustering
   - **Networking**: Public endpoint (or VNet for production)

3. **Review + Create** → Wait 10-15 minutes for deployment

4. **Get Connection Details**:
   - Go to resource → "Access keys" blade
   - Copy:
     - **Host name**: `toolweaver-cache.redis.cache.windows.net`
     - **Primary access key**: (long string)
     - **SSL Port**: 6380 (required)

5. **Configure ToolWeaver**:
```bash
# .env file
REDIS_URL=rediss://toolweaver-cache.redis.cache.windows.net:6380
REDIS_PASSWORD=your-primary-access-key-here
```

### Setup via Azure CLI

```bash
# Login
az login

# Create resource group
az group create --name rg-toolweaver --location eastus

# Create Redis Cache (Standard C1)
az redis create \
  --name toolweaver-cache \
  --resource-group rg-toolweaver \
  --location eastus \
  --sku Standard \
  --vm-size C1 \
  --enable-non-ssl-port false

# Get connection details
az redis list-keys --name toolweaver-cache --resource-group rg-toolweaver

# Show hostname
az redis show --name toolweaver-cache --resource-group rg-toolweaver \
  --query "hostName" -o tsv
```

### Test Connection

```powershell
# Install redis-cli for Windows
# Or use Python test

# From project directory with venv activated
.\.venv\Scripts\Activate.ps1
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()
client = redis.Redis(
    host='toolweaver-cache.redis.cache.windows.net',
    port=6380,
    password=os.getenv('REDIS_PASSWORD'),
    ssl=True,
    ssl_cert_reqs=None
)
print(client.ping())  # Should print True
"
```

### Monitoring Azure Redis

```bash
# Get metrics
az monitor metrics list \
  --resource $(az redis show --name toolweaver-cache --resource-group rg-toolweaver --query id -o tsv) \
  --metric "ConnectedClients,UsedMemory,CacheHits,CacheMisses" \
  --interval PT1M

# View logs (requires diagnostic settings)
az monitor diagnostic-settings create \
  --name redis-diagnostics \
  --resource $(az redis show --name toolweaver-cache --resource-group rg-toolweaver --query id -o tsv) \
  --logs '[{"category":"ConnectedClientList","enabled":true}]' \
  --workspace your-log-analytics-workspace-id
```

### Cost Management

```bash
# Stop (deallocate) Redis when not in use - NOT SUPPORTED
# Azure Redis cannot be stopped, only deleted

# Delete to stop charges
az redis delete --name toolweaver-cache --resource-group rg-toolweaver --yes

# To resume: Recreate (data will be lost)
```

**Cost Estimation**:
- **Basic C0**: ~$18/month (730 hours)
- **Standard C1**: ~$45/month
- **Premium P1**: ~$266/month

**Recommendation for ToolWeaver**:
- **Development**: Local Docker/WSL (free)
- **Testing**: Azure Basic C0 or Standard C1
- **Production**: Azure Standard C1+ or Premium (with clustering)

---

## Option 4: Redis Cloud (Free Tier) ⭐ Recommended for Development

### Free Tier Limits
- **Memory**: 30 MB
- **Connections**: 30 concurrent
- **Bandwidth**: Unlimited
- **Availability**: Always on
- **Cost**: $0/month forever
- **Perfect for**: Development, testing, proof of concepts

### Setup

1. **Create Redis Cloud Account**:
   - Go to [https://redis.io/cloud](https://redis.io/cloud)
   - Click "Try Free"
   - Sign up with Google/GitHub or email (no credit card required)

2. **Create Free Database**:
   - Click "New Database"
   - **Name**: `toolweaver-cache`
   - **Cloud**: AWS or Google Cloud
   - **Region**: Choose nearest (e.g., us-east-1)
   - **Type**: Redis Stack (includes JSON, Search modules)
   - **Plan**: Select **"Free"** (30 MB)
   - Click "Activate"
   - Wait 2-3 minutes for provisioning

3. **Get Connection Details**:
   - Click on your database
   - Copy:
     - **Public endpoint**: `redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345`
     - **Default user password**: Click "View" icon → Copy password

4. **Configure ToolWeaver**:
```bash
# .env file
REDIS_URL=redis://redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345
REDIS_PASSWORD=your-password-here
```

### Test Connection

```powershell
# From project directory with venv activated
.\.venv\Scripts\Activate.ps1
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()
# Parse URL to get host and port
url = os.getenv('REDIS_URL')
host = url.split('//')[1].split(':')[0]
port = int(url.split(':')[-1])

client = redis.Redis(
    host=host,
    port=port,
    password=os.getenv('REDIS_PASSWORD'),
    ssl=False,
    decode_responses=True
)
print(client.ping())  # Should print True
print(f'Memory: {client.info(\"memory\")[\"used_memory_human\"]}')
"
```

### Monitoring Redis Cloud

- **Dashboard**: https://app.redislabs.com
- **Metrics**: Memory usage, operations/sec, latency
- **Alerts**: Email notifications for high memory
- **Logs**: Connection logs and slow queries

### 30 MB Capacity Planning

**What fits in 30 MB?**
- ~5,000 tool catalog entries (6 KB each)
- ~30,000 search result caches (1 KB each)
- ~75,000 small embeddings cached (400 bytes each)

**Cache Strategy for 30 MB Limit**:
```python
# Prioritize frequently-used caches
tool_cache.CATALOG_TTL = 6 * 3600   # 6 hours (vs 24h)
tool_cache.SEARCH_TTL = 30 * 60     # 30 min (vs 1h)
tool_cache.EMBEDDING_TTL = 24 * 3600  # 24 hours (vs 7d)
```

### Upgrade When Needed
- **Paid Plans**: Start at $7/month (100 MB)
- **Essentials**: $7-200/month (100 MB - 50 GB)
- **Pro**: Custom pricing (>50 GB, multi-AZ, clustering)

---

## Configuration Comparison

| Feature | Docker | WSL | Redis Cloud (Free) | Azure Redis |
|---------|--------|-----|--------------------|-------------|
| **Cost** | Free | Free | Free (30 MB) | ~$18-266/month |
| **Setup Time** | 2 min | 10 min | 5 min | 15 min |
| **Memory** | Unlimited | Unlimited | 30 MB | 250 MB - 120 GB |
| **Persistence** | Yes (volume) | Yes (disk) | Yes (RDB+AOF) | Yes (RDB+AOF) |
| **Clustering** | No | No | No | Yes (Premium) |
| **TLS/SSL** | Optional | Optional | Optional | Required |
| **Scalability** | Single node | Single node | Single node | Up to 10 shards |
| **Availability** | None | None | 99.99% SLA | 99.9% SLA |
| **Monitoring** | Basic | Basic | Cloud dashboard | Azure Monitor |
| **Best For** | Dev | Dev/Test | Dev/Small prod | Production |

---

## Automatic Detection in ToolWeaver

ToolWeaver automatically detects Redis availability:

```python
from orchestrator.redis_cache import RedisCache

# Initialize (tries Redis, falls back to file cache)
cache = RedisCache(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    password=os.getenv("REDIS_PASSWORD"),
    enable_fallback=True  # File cache fallback
)

# Check status
status = cache.health_check()
print(f"Redis available: {status['redis_available']}")
print(f"Circuit breaker: {status['circuit_breaker_state']}")
```

**Fallback Behavior**:
- If Redis unavailable → Uses file cache automatically
- Circuit breaker prevents hammering failed Redis
- Logs warnings but continues operation
- No code changes needed when switching between local/Azure

---

## Environment Variables Summary

```bash
# .env file

# Option 1: Local Docker
REDIS_URL=redis://localhost:6379

# Option 2: WSL
REDIS_URL=redis://172.xx.xx.xx:6379

# Option 3: Azure Cache for Redis
REDIS_URL=rediss://toolweaver-cache.redis.cache.windows.net:6380

# Option 4: Redis Cloud (Free Tier)
REDIS_URL=redis://redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345
REDIS_PASSWORD=your-redis-cloud-password
REDIS_PASSWORD=your-azure-redis-access-key
```

---

## Troubleshooting

### Docker: Connection Refused
```powershell
# Check if container is running
docker ps -a | Select-String redis

# View logs
docker logs toolweaver-redis

# Restart
docker-compose restart redis
```

### WSL: Can't Connect from Windows
```bash
# In WSL, check if Redis is listening on 0.0.0.0
sudo netstat -tlnp | grep redis

# Should show: 0.0.0.0:6379

# If showing 127.0.0.1:6379, edit config:
sudo nano /etc/redis/redis.conf
# Change: bind 127.0.0.1 to bind 0.0.0.0
sudo systemctl restart redis-server
```

### Azure: SSL Certificate Error
```python
# Use ssl_cert_reqs=None for development
client = redis.Redis(
    host='your-cache.redis.cache.windows.net',
    port=6380,
    password='your-key',
    ssl=True,
    ssl_cert_reqs=None  # Disable cert verification
)
```

### Azure: Timeout Issues
- Check firewall rules: Azure Portal → Redis → Firewall → Add client IP
- Verify SSL port 6380 (not 6379)
- Check if VNet restricts access

---

## Next Steps

1. Choose deployment option
2. Set environment variables in `.env`
3. Run tests: `pytest tests/test_redis_cache.py -v`
4. Monitor cache hit rates in logs

ToolWeaver will automatically use Redis when available and fall back to file cache if needed.
