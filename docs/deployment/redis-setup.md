# Redis Setup Guide

Distributed caching options for development through production.

## Option 1: Local Redis via Docker (Windows/Linux/macOS)
```bash
# From repo root
docker compose up -d redis
# Verify
docker ps | grep redis
# Configure
REDIS_URL=redis://localhost:6379
```
Stop: `docker compose stop redis`

## Option 2: Local Redis via WSL 2 (Windows)
Install Redis in WSL, bind to 0.0.0.0 if you need Windows access, and set:
```
REDIS_URL=redis://<wsl-ip>:6379
```
Test with `redis-cli ping`.

## Option 3: Redis Cloud (Free Tier) — good for dev
- Create free db at https://redis.io/cloud (30 MB limit).
- Configure:
```
REDIS_URL=redis://<host>:<port>
REDIS_PASSWORD=<password>
```
Test with a small Python ping script.

## Option 4: Azure Cache for Redis (production)
Portal or CLI:
```bash
az group create --name rg-toolweaver --location eastus
az redis create --name toolweaver-cache --resource-group rg-toolweaver --location eastus --sku Standard --vm-size C1 --enable-non-ssl-port false
az redis list-keys --name toolweaver-cache --resource-group rg-toolweaver
```
Config:
```
REDIS_URL=rediss://toolweaver-cache.redis.cache.windows.net:6380
REDIS_PASSWORD=<primary-key>
```

## Monitoring & costs
- Redis Cloud free: 30 MB, great for dev.
- Azure: C0/C1 for test; Premium for clustering/production.
- Use Azure Monitor or Redis Cloud dashboards for metrics.

## ToolWeaver behavior
`RedisCache` can fall back to file cache if Redis is unavailable; health checks report availability and circuit breaker state.
