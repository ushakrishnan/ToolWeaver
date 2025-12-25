# Qdrant Setup Guide

Vector database options for semantic search.

## Option 1: Local Qdrant via Docker
```bash
# From repo root
docker compose up -d qdrant
# Verify
curl http://localhost:6333/collections
# Configure
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```
Data persists in `./qdrant_data` if configured in compose.

## Option 2: Local Qdrant via WSL 2
Run the container in WSL Docker, find the WSL IP (e.g., `ip addr show eth0`), then configure:
```
QDRANT_URL=http://<wsl-ip>:6333
QDRANT_API_KEY=
```

## Option 3: Qdrant Cloud (Free Tier) — recommended for dev
- Create free 1 GB cluster at https://cloud.qdrant.io (≈100k vectors, ~2.6k tools at 384-dim).
- Configure:
```
QDRANT_URL=https://<cluster>.aws.cloud.qdrant.io
QDRANT_API_KEY=<key>
```
- Create collection `toolweaver_tools` (384 dims, cosine, dense vector `default`; sparse not required by code).

## Option 4: Azure Container Instances (self-hosted cloud)
```bash
az group create --name rg-toolweaver --location eastus
az container create --resource-group rg-toolweaver --name qdrant-instance --image qdrant/qdrant:latest --cpu 1 --memory 2 --ports 6333 6334 --dns-name-label toolweaver-qdrant --location eastus --restart-policy Always
az container show --resource-group rg-toolweaver --name qdrant-instance --query "ipAddress.fqdn" -o tsv
```
Config:
```
QDRANT_URL=http://toolweaver-qdrant.eastus.azurecontainer.io:6333
QDRANT_API_KEY=<key-if-set>
```

## Capacity & monitoring
- Free tier: 1 GB (~100k vectors @384 dims). Upgrade when you need more.
- Use Qdrant Cloud dashboard metrics; for self-hosted, expose /metrics if desired.

## ToolWeaver behavior
`VectorToolSearchEngine` falls back to in-memory search if Qdrant is unavailable; index the catalog after configuring Qdrant for best results.
