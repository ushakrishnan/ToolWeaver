# Qdrant Setup Guide for ToolWeaver Phase 7

This guide covers setting up Qdrant vector database with four deployment options.

---

## Option 1: Local Qdrant with Docker (Windows)

### Prerequisites
- Docker Desktop for Windows installed

### Setup

1. **Start Qdrant with docker-compose**:
```powershell
cd C:\Usha\UKRepos\ToolWeaver
docker-compose up -d qdrant
```

2. **Verify Qdrant is running**:
```powershell
docker ps | Select-String qdrant
# Should show: toolweaver-qdrant running on ports 6333, 6334
```

3. **Test connection**:
```powershell
# Open browser
Start-Process "http://localhost:6333/dashboard"

# Or test with curl
curl http://localhost:6333/collections
```

4. **Configure ToolWeaver**:
```bash
# .env file
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
```

### Stop Qdrant
```powershell
docker-compose stop qdrant
```

### Data Persistence
- Data stored in `./qdrant_data` directory
- Survives container restarts
- Backup: Copy `./qdrant_data` folder

---

## Option 2: Local Qdrant with WSL 2

### Prerequisites
- WSL 2 installed (`wsl --install`)
- Docker installed in WSL

### Setup

1. **Install Docker in WSL**:
```bash
# Open WSL terminal
wsl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Docker
sudo service docker start
```

2. **Run Qdrant container**:
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

3. **Find WSL IP address**:
```bash
ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1
# Example output: 172.xx.xx.xx
```

4. **Configure ToolWeaver (from Windows)**:
```bash
# .env file
QDRANT_URL=http://172.xx.xx.xx:6333
QDRANT_API_KEY=
```

### Access from Windows
```powershell
# Test from PowerShell
curl http://172.xx.xx.xx:6333/collections
```

---

## Option 3: Qdrant Cloud (Free Tier) ⭐ Recommended for Development

### Free Tier Limits
- **Storage**: 1 GB cluster
- **Vectors**: Up to 100,000 vectors
- **Collections**: Unlimited
- **Availability**: Always on
- **Cost**: $0/month forever
- **Perfect for**: Development, testing, small projects (up to 2,600 tools with 384-dim embeddings)

### Setup

1. **Create Qdrant Cloud Account**:
   - Go to [https://cloud.qdrant.io](https://cloud.qdrant.io)
   - Click "Sign Up" (free, no credit card required)
   - Sign up with GitHub/Google or email

2. **Create Free Cluster**:
   - Click "Create Cluster"
   - **Name**: `toolweaver-dev`
   - **Region**: Choose nearest (e.g., AWS us-east-1)
   - **Plan**: Select **"Free"** (1 GB)
   - Click "Create"
   - Wait 2-3 minutes for provisioning

3. **Get Connection Details**:
   - Click on your cluster
   - Copy:
     - **Cluster URL**: `https://xxxxx.us-east-1-0.aws.cloud.qdrant.io`
     - **API Key**: Click "Generate API Key" → Copy key (save it, shown only once!)

4. **Configure ToolWeaver**:
```bash
# .env file
QDRANT_URL=https://xxxxx.us-east-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=your-api-key-here
```

### Test Connection

```powershell
# From project directory with venv activated
.\.venv\Scripts\Activate.ps1
python -c "
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)
print(client.get_collections())
"
```

### Monitoring Qdrant Cloud

- **Dashboard**: https://cloud.qdrant.io
- **Usage**: View storage, vectors, requests
- **Metrics**: Collection sizes, query latency
- **Logs**: Request history and errors

### Upgrade When Needed
- **Paid Plans**: Start at $25/month (5 GB)
- **Vertical Scaling**: Up to 32 GB RAM
- **Horizontal Scaling**: Add replicas

---

## Option 4: Azure Container Instances (Cloud Self-Hosted)

### Prerequisites
- Azure subscription
- Azure CLI installed (`az login`)

### Setup

1. **Create Resource Group**:
```bash
az group create --name rg-toolweaver --location eastus
```

2. **Deploy Qdrant Container**:
```bash
az container create \
  --resource-group rg-toolweaver \
  --name qdrant-instance \
  --image qdrant/qdrant:latest \
  --cpu 1 \
  --memory 2 \
  --ports 6333 6334 \
  --dns-name-label toolweaver-qdrant \
  --location eastus \
  --restart-policy Always
```

3. **Get Public IP**:
```bash
az container show \
  --resource-group rg-toolweaver \
  --name qdrant-instance \
  --query "ipAddress.fqdn" -o tsv
# Output: toolweaver-qdrant.eastus.azurecontainer.io
```

4. **Configure ToolWeaver**:
```bash
# .env file
QDRANT_URL=http://toolweaver-qdrant.eastus.azurecontainer.io:6333
QDRANT_API_KEY=  # Add API key in production
```

### Cost
- **1 vCPU, 2 GB RAM**: ~$30/month (730 hours)
- **2 vCPU, 4 GB RAM**: ~$60/month
- Stop when not in use to save costs

### Stop/Start
```bash
# Stop (deallocate)
az container stop --resource-group rg-toolweaver --name qdrant-instance

# Start
az container start --resource-group rg-toolweaver --name qdrant-instance

# Delete
az container delete --resource-group rg-toolweaver --name qdrant-instance --yes
```

---

## Configuration Comparison

| Feature | Docker | WSL | Qdrant Cloud (Free) | Azure ACI |
|---------|--------|-----|---------------------|-----------|
| **Cost** | Free | Free | Free (1 GB) | ~$30/month |
| **Setup Time** | 2 min | 10 min | 5 min | 10 min |
| **Storage** | Unlimited | Unlimited | 1 GB (100k vectors) | 2-4 GB |
| **Availability** | Local only | Local only | 99.9% SLA | 99.9% SLA |
| **Performance** | Fast | Fast | <10ms queries | <20ms queries |
| **Persistence** | Yes (volume) | Yes (disk) | Yes (cloud) | Optional (volume) |
| **Backup** | Manual | Manual | Automatic | Manual |
| **API Key** | Optional | Optional | Required | Optional |
| **Best For** | Dev | Dev | Dev/Small prod | Production |

---

## Capacity Planning

### 384-dim Embeddings (all-MiniLM-L6-v2)

| Storage | Max Vectors | Max Tools | Use Case |
|---------|-------------|-----------|----------|
| 1 GB (Free) | 100,000 | ~2,600 | Development, small projects |
| 5 GB (Paid) | 500,000 | ~13,000 | Medium projects |
| 20 GB (Paid) | 2,000,000 | ~52,000 | Large projects |

**Calculation**: 384 dims × 4 bytes + metadata ≈ 400 KB per 1000 vectors

---

## Migration Between Options

### From Local Docker to Qdrant Cloud

1. **Export collections**:
```python
from qdrant_client import QdrantClient

# Source (local)
source = QdrantClient(url="http://localhost:6333")
collections = source.get_collections()

# Destination (cloud)
dest = QdrantClient(
    url="https://xxxxx.aws.cloud.qdrant.io",
    api_key="your-key"
)

# Copy collections
for collection in collections.collections:
    # Export from source
    points = source.scroll(collection_name=collection.name, limit=10000)
    
    # Import to destination
    dest.upsert(
        collection_name=collection.name,
        points=points[0]
    )
```

2. **Update .env**:
```bash
# Old
QDRANT_URL=http://localhost:6333

# New
QDRANT_URL=https://xxxxx.aws.cloud.qdrant.io
QDRANT_API_KEY=your-api-key
```

---

## Automatic Detection in ToolWeaver

ToolWeaver automatically detects Qdrant availability:

```python
from orchestrator.vector_search import VectorToolSearchEngine

# Initialize (tries Qdrant, falls back to in-memory)
search_engine = VectorToolSearchEngine(
    qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    fallback_to_memory=True
)

# Index catalog
search_engine.index_catalog(catalog)

# Search (uses Qdrant if available, else in-memory)
results = search_engine.search("github pull request", catalog, top_k=5)
```

---

## Security Best Practices

### Local Development
- No API key needed
- Bind to localhost only
- Use firewall rules

### Production (Cloud)
```bash
# .env
QDRANT_URL=https://xxxxx.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-secret-key  # Never commit to git!

# Use environment variables, not .env in production
export QDRANT_URL="https://..."
export QDRANT_API_KEY="..."
```

### API Key Rotation
1. Generate new key in Qdrant Cloud dashboard
2. Update environment variables
3. Delete old key

---

## Troubleshooting

### Docker: Port Already in Use
```powershell
# Find process using port 6333
Get-NetTCPConnection -LocalPort 6333

# Stop conflicting container
docker stop $(docker ps -q --filter "publish=6333")
```

### WSL: Can't Connect from Windows
```bash
# Check if Qdrant is listening
docker logs qdrant

# Verify port forwarding
curl http://localhost:6333/collections
```

### Qdrant Cloud: Connection Timeout
- Verify API key is correct
- Check cluster status in dashboard
- Ensure QDRANT_URL includes `https://` (not `http://`)
- Check firewall/VPN settings

### Azure ACI: Container Not Starting
```bash
# View logs
az container logs --resource-group rg-toolweaver --name qdrant-instance

# Check events
az container show --resource-group rg-toolweaver --name qdrant-instance
```

---

## Performance Optimization

### Batch Indexing
```python
# Index 1000 tools in one batch (faster)
search_engine.index_catalog(catalog, batch_size=64)
```

### Pre-compute Embeddings
```python
# At application startup
def warm_up():
    search_engine._init_embedding_model()
    search_engine.index_catalog(catalog)
    logger.info("Qdrant warm-up complete")
```

### Query Optimization
```python
# Use domain filtering for 10x faster search
results = search_engine.search(
    "create PR",
    catalog,
    domain="github",  # Search only GitHub tools
    top_k=5
)
```

---

## Cost Comparison

### Monthly Costs (assuming 24/7 operation)

| Option | Storage | Cost/Month | Notes |
|--------|---------|------------|-------|
| **Docker (Local)** | Unlimited | $0 | Electricity costs only |
| **WSL (Local)** | Unlimited | $0 | Electricity costs only |
| **Qdrant Cloud Free** | 1 GB | $0 | Perfect for dev/test |
| **Qdrant Cloud Paid** | 5 GB | $25 | Production ready |
| **Azure ACI (1 vCPU)** | 2 GB | $30 | Self-hosted cloud |

**Recommendation**:
- **Development**: Qdrant Cloud Free (no setup, always available)
- **Testing**: Local Docker (full control, no limits)
- **Production**: Qdrant Cloud Paid ($25-95/mo based on scale)

---

## Next Steps

1. Choose deployment option
2. Set environment variables in `.env`
3. Run tests: `pytest tests/test_vector_search.py -v`
4. Index your tool catalog
5. Monitor performance and storage usage

ToolWeaver will automatically use Qdrant when available and fall back to in-memory search if needed.
