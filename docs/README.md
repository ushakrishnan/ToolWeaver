# ToolWeaver Documentation

Complete documentation for ToolWeaver's features, deployment, and usage.

---

## 📚 Documentation Index

### 🚀 Getting Started

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Configuration Guide](CONFIGURATION.md)** | Complete setup for all LLM providers (Azure OpenAI, OpenAI, Claude, Gemini, Ollama, Azure AI Foundry) | **Start here** - Set up your first deployment |
| **[Quick Reference](QUICK_REFERENCE.md)** | Common patterns, code snippets, and quick examples | Need a fast reference for common tasks |
| **[FREE_TIER_SETUP.md](FREE_TIER_SETUP.md)** | Get started with free tier providers (no credit card needed) | Want to try ToolWeaver without costs |

### 💡 Core Features

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Features Guide](FEATURES_GUIDE.md)** | Complete feature overview with performance metrics, capabilities, and examples | Want comprehensive understanding of all features |
| **[Workflow System Guide](WORKFLOW_USAGE_GUIDE.md)** | Workflow composition, pattern recognition, dependency resolution, and library management | Building multi-step tool chains |
| **[Two-Model Architecture](TWO_MODEL_ARCHITECTURE.md)** | Cost-optimized design: large planner + small executor, with cost comparisons | Understanding the cost/performance strategy |
| **[Prompt Caching Best Practices](PROMPT_CACHING.md)** | Reduce costs by 90% with prompt caching strategies for Anthropic and OpenAI | Optimizing costs for production |
| **[Search Tuning Guide](SEARCH_TUNING.md)** | Optimize semantic search: strategies (hybrid/BM25/embeddings), thresholds, performance | Improving tool selection accuracy |

### 🔧 Deployment & Production

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)** | Deploy to Azure with security hardening, monitoring, scaling, and troubleshooting | **Essential for production** - Security, monitoring, scaling |
| **[Security Guide](SECURITY.md)** | Security best practices, AST validation, sandboxing, authentication | Securing production deployments |
| **[Azure Computer Vision Setup](AZURE_SETUP.md)** | Configure Azure Computer Vision for real OCR (receipt extraction, document processing) | Need production-grade OCR |
| **[Small Model Improvements](SMALL_MODEL_IMPROVEMENTS.md)** | Enhanced Phi-3 JSON parsing, Azure CV integration, local model optimization | Using small models or Phi-3 |

### 🗄️ Scaling & Infrastructure

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Qdrant Setup](QDRANT_SETUP.md)** | Vector database setup for 1000+ tool catalogs | Scaling beyond 300 tools |
| **[Redis Setup](REDIS_SETUP.md)** | Distributed cache setup for multi-instance deployments | Running multiple instances |

### 🏗️ Architecture & Technical

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Architecture Details](ARCHITECTURE.md)** | Technical deep dive: hybrid dispatcher, tool types, execution flow | Understanding internals |
| **[Workflow Architecture](WORKFLOW_ARCHITECTURE.md)** | Workflow engine design: dependency resolution, parallel execution, pattern detection | Building on workflow system |
| **[Implementation Details](IMPLEMENTATION.md)** | Internal architecture and technical specifications | **For contributors** - Working on ToolWeaver itself |

### 🔄 Migration & Maintenance

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[Migration Guide](MIGRATION_GUIDE.md)** | Upgrade guides, breaking changes, backward compatibility | Upgrading from older versions |

---

## 📖 Reading Paths

### Path 1: Quick Start (30 minutes)
Perfect for trying ToolWeaver quickly:

1. **[FREE_TIER_SETUP.md](FREE_TIER_SETUP.md)** - Set up with free providers
2. **[Quick Reference](QUICK_REFERENCE.md)** - Run your first examples
3. **[Features Guide](FEATURES_GUIDE.md)** - Explore capabilities

### Path 2: Production Deployment (2-3 hours)
For deploying to production:

1. **[Configuration Guide](CONFIGURATION.md)** - Set up your LLM providers
2. **[Features Guide](FEATURES_GUIDE.md)** - Understand all capabilities
3. **[Two-Model Architecture](TWO_MODEL_ARCHITECTURE.md)** - Optimize costs
4. **[Prompt Caching Best Practices](PROMPT_CACHING.md)** - Reduce costs 90%
5. **[Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)** - Deploy securely
6. **[Security Guide](SECURITY.md)** - Harden your deployment

### Path 3: Advanced Features (1-2 hours)
For building complex workflows:

1. **[Workflow System Guide](WORKFLOW_USAGE_GUIDE.md)** - Multi-step tool chains
2. **[Workflow Architecture](WORKFLOW_ARCHITECTURE.md)** - Technical design
3. **[Search Tuning Guide](SEARCH_TUNING.md)** - Optimize tool selection
4. **[Qdrant Setup](QDRANT_SETUP.md)** - Scale to 1000+ tools

### Path 4: Contributing (2-4 hours)
For developers working on ToolWeaver:

1. **[Architecture Details](ARCHITECTURE.md)** - System design
2. **[Implementation Details](IMPLEMENTATION.md)** - Codebase structure
3. **[Workflow Architecture](WORKFLOW_ARCHITECTURE.md)** - Workflow internals

---

## 🎯 Find What You Need

### By Use Case

**"I want to try ToolWeaver for free"**
→ [FREE_TIER_SETUP.md](FREE_TIER_SETUP.md)

**"I need to deploy to production"**
→ [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md) + [Security Guide](SECURITY.md)

**"My costs are too high"**
→ [Two-Model Architecture](TWO_MODEL_ARCHITECTURE.md) + [Prompt Caching](PROMPT_CACHING.md)

**"I need to build multi-step workflows"**
→ [Workflow System Guide](WORKFLOW_USAGE_GUIDE.md)

**"Tool selection isn't accurate"**
→ [Search Tuning Guide](SEARCH_TUNING.md)

**"I have 500+ tools"**
→ [Qdrant Setup](QDRANT_SETUP.md)

**"I need to process receipts/documents"**
→ [Azure Computer Vision Setup](AZURE_SETUP.md)

**"I want to understand how it works"**
→ [Features Guide](FEATURES_GUIDE.md) + [Architecture Details](ARCHITECTURE.md)

### By Provider

**Azure OpenAI / Azure AI Foundry**
→ [Configuration Guide](CONFIGURATION.md) + [Azure CV Setup](AZURE_SETUP.md)

**OpenAI**
→ [Configuration Guide](CONFIGURATION.md) + [Prompt Caching](PROMPT_CACHING.md)

**Anthropic Claude**
→ [Configuration Guide](CONFIGURATION.md) + [Prompt Caching](PROMPT_CACHING.md)

**Local Models (Ollama, Phi-3)**
→ [Configuration Guide](CONFIGURATION.md) + [Small Model Improvements](SMALL_MODEL_IMPROVEMENTS.md)

---

## 📊 Document Statistics

| Category | Files | Total Lines |
|----------|-------|-------------|
| Getting Started | 3 | ~1,200 |
| Core Features | 5 | ~3,500 |
| Deployment | 4 | ~2,800 |
| Scaling | 2 | ~800 |
| Architecture | 3 | ~1,500 |
| Migration | 1 | ~400 |
| **Total** | **18** | **~10,200** |

---

## 🆘 Need Help?

- **Quick questions**: Check [Quick Reference](QUICK_REFERENCE.md)
- **Setup issues**: See [Configuration Guide](CONFIGURATION.md)
- **Production problems**: See [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- **Security concerns**: See [Security Guide](SECURITY.md)
- **Cost optimization**: See [Two-Model Architecture](TWO_MODEL_ARCHITECTURE.md) + [Prompt Caching](PROMPT_CACHING.md)

---

## 📝 Documentation Maintenance

This documentation is organized by **user needs** and **use cases** rather than development phases.

**For contributors**: When adding new documentation:
1. Add entry to this README with description and "When to Read"
2. Update the appropriate reading path
3. Add to "Find What You Need" if it addresses a common use case
4. Keep entries concise but informative
