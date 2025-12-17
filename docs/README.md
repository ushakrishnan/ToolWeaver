# ToolWeaver Documentation

Welcome to the ToolWeaver documentation! This guide is organized by audience and use case.

## 🧭 Quick Navigation

**👤 New User?** → Start with [User Guide](#-user-guide)  
**👨‍💻 Contributing?** → See [Developer Guide](#-developer-guide)  
**🚀 Deploying?** → Check [Deployment](#-deployment)  
**📚 Deep Dive?** → Browse [Reference](#-reference)

---

## 👤 User Guide

*For users installing ToolWeaver via `pip install toolweaver`*

| Document | Description | Time |
|----------|-------------|------|
| [Getting Started](user-guide/GETTING_STARTED.md) | Step-by-step tutorial for new users | 10 min |
| [Configuration](user-guide/CONFIGURATION.md) | Configure API providers and settings | 15 min |
| [Features Guide](user-guide/FEATURES_GUIDE.md) | Complete feature reference | 30 min |
| [Workflow Usage](user-guide/WORKFLOW_USAGE_GUIDE.md) | Build and compose workflows | 20 min |
| [Quick Reference](user-guide/QUICK_REFERENCE.md) | Common commands and patterns | 5 min |
| [Free Tier Setup](user-guide/FREE_TIER_SETUP.md) | Use free services (Qdrant, Redis) | 10 min |

**Start here:** [Getting Started](user-guide/GETTING_STARTED.md)

---

## 👨‍💻 Developer Guide

*For contributors modifying ToolWeaver source code*

| Document | Description | Time |
|----------|-------------|------|
| [Architecture](developer-guide/ARCHITECTURE.md) | System design and components | 30 min |
| [Implementation](developer-guide/IMPLEMENTATION.md) | Code structure and patterns | 20 min |
| [Security](developer-guide/SECURITY.md) | Security model and sandboxing | 15 min |
| [Publishing](developer-guide/PUBLISHING.md) | Package release process | 10 min |

**Prerequisites:**
- Read [../CONTRIBUTING.md](../CONTRIBUTING.md) first
- Setup: `git clone` + `pip install -e .`
- Explore: [../examples/](../examples/)

---

## 🚀 Deployment

*For deploying ToolWeaver to production environments*

| Document | Description | Time |
|----------|-------------|------|
| [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md) | Deploy to production | 45 min |
| [Azure Setup](deployment/AZURE_SETUP.md) | Configure Azure services | 30 min |
| [Redis Setup](deployment/REDIS_SETUP.md) | Deploy Redis caching | 15 min |
| [Qdrant Setup](deployment/QDRANT_SETUP.md) | Deploy vector search | 20 min |

**Best Practice:** Test locally with [samples/](../samples/) before deploying.

---

## 📚 Reference

*Technical deep-dives and advanced topics*

| Document | Description | Audience |
|----------|-------------|----------|
| [Two-Model Architecture](reference/TWO_MODEL_ARCHITECTURE.md) | Large + small model design | Advanced |
| [Workflow Architecture](reference/WORKFLOW_ARCHITECTURE.md) | Workflow engine internals | Advanced |
| [Prompt Caching](reference/PROMPT_CACHING.md) | Cost optimization techniques | All |
| [Search Tuning](reference/SEARCH_TUNING.md) | Optimize tool search | Advanced |
| [Migration Guide](reference/MIGRATION_GUIDE.md) | Upgrade between versions | All |
| [Small Model Improvements](reference/SMALL_MODEL_IMPROVEMENTS.md) | Enhance small models | Advanced |

---

## 📖 Additional Resources

### Samples & Examples
- [samples/](../samples/) - Ready-to-run examples using installed package
- [examples/](../examples/) - Development examples using source code

### Project Documentation
- [../README.md](../README.md) - Main project overview
- [../CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [RELEASES.md](RELEASES.md) - Version history (local only)
- [DOCUMENTATION_BEST_PRACTICES.md](DOCUMENTATION_BEST_PRACTICES.md) - Doc standards

### External Links
- [PyPI Package](https://pypi.org/project/toolweaver/)
- [GitHub Repository](https://github.com/ushakrishnan/ToolWeaver)
- [Anthropic MCP](https://modelcontextprotocol.io/) - Inspiration

---

## 🗺️ Documentation Map

```
docs/
├── README.md (this file)              # Navigation hub
│
├── user-guide/                        # 👤 For package users
│   ├── GETTING_STARTED.md            # Start here!
│   ├── CONFIGURATION.md              # Setup
│   ├── FEATURES_GUIDE.md             # What's available
│   ├── WORKFLOW_USAGE_GUIDE.md       # Build workflows
│   ├── QUICK_REFERENCE.md            # Cheat sheet
│   └── FREE_TIER_SETUP.md            # Free services
│
├── developer-guide/                   # 👨‍💻 For contributors
│   ├── ARCHITECTURE.md               # How it works
│   ├── IMPLEMENTATION.md             # Code structure
│   ├── SECURITY.md                   # Security model
│   └── PUBLISHING.md                 # Release process
│
├── deployment/                        # 🚀 For production
│   ├── PRODUCTION_DEPLOYMENT.md      # Deploy guide
│   ├── AZURE_SETUP.md                # Azure config
│   ├── REDIS_SETUP.md                # Cache setup
│   └── QDRANT_SETUP.md               # Vector DB
│
└── reference/                         # 📚 Technical details
    ├── TWO_MODEL_ARCHITECTURE.md     # Design patterns
    ├── WORKFLOW_ARCHITECTURE.md      # Internals
    ├── PROMPT_CACHING.md             # Optimization
    ├── SEARCH_TUNING.md              # Tuning guide
    ├── MIGRATION_GUIDE.md            # Upgrades
    └── SMALL_MODEL_IMPROVEMENTS.md   # Enhancements
```

---

## 🎯 Learning Paths

### Path 1: Quick Start (New User)
1. [Getting Started](user-guide/GETTING_STARTED.md) - 10 min
2. [Configuration](user-guide/CONFIGURATION.md) - 15 min
3. Try [samples/01-basic-receipt-processing](../samples/01-basic-receipt-processing/)
4. Browse [Features Guide](user-guide/FEATURES_GUIDE.md)

### Path 2: Deep Understanding (Advanced User)
1. [Features Guide](user-guide/FEATURES_GUIDE.md) - 30 min
2. [Two-Model Architecture](reference/TWO_MODEL_ARCHITECTURE.md) - 20 min
3. [Workflow Architecture](reference/WORKFLOW_ARCHITECTURE.md) - 20 min
4. [Prompt Caching](reference/PROMPT_CACHING.md) - 15 min

### Path 3: Contributor (Developer)
1. [../CONTRIBUTING.md](../CONTRIBUTING.md) - 20 min
2. [Architecture](developer-guide/ARCHITECTURE.md) - 30 min
3. [Implementation](developer-guide/IMPLEMENTATION.md) - 20 min
4. Try [examples/](../examples/)

### Path 4: Production Deployment
1. [Configuration](user-guide/CONFIGURATION.md) - 15 min
2. [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md) - 45 min
3. [Azure Setup](deployment/AZURE_SETUP.md) - 30 min
4. [Redis Setup](deployment/REDIS_SETUP.md) + [Qdrant Setup](deployment/QDRANT_SETUP.md) - 35 min

---

## ❓ Need Help?

**Can't find what you need?**
1. Use the search function (Ctrl+F) in relevant section
2. Check [../README.md](../README.md) for overview
3. Browse [samples/](../samples/) for examples
4. Search [GitHub Issues](https://github.com/ushakrishnan/ToolWeaver/issues)
5. Create a new issue if needed

**Contributing to docs?**
- See [DOCUMENTATION_BEST_PRACTICES.md](DOCUMENTATION_BEST_PRACTICES.md)
- Follow [../CONTRIBUTING.md](../CONTRIBUTING.md) guidelines

---

## 📝 Documentation Standards

- **User Guide**: Task-oriented, step-by-step, beginner-friendly
- **Developer Guide**: Architecture, patterns, contribution workflows
- **Deployment**: Production setup, configuration, best practices
- **Reference**: Technical details, deep-dives, advanced topics

All documentation follows the standards in [DOCUMENTATION_BEST_PRACTICES.md](DOCUMENTATION_BEST_PRACTICES.md).

---

**Last Updated:** December 17, 2024  
**Version:** 0.1.3
