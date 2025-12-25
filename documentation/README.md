# ToolWeaver Documentation (Legacy)

Note: This folder is legacy/internal and is **not published**. The MkDocs site builds only from `docs/` (see `docs_dir` in mkdocs.yml).

**Project Status:** ✅ ALL PHASES COMPLETE (0-4)  
**Test Results:** 971/985 passing (98.6%) | Coverage: 67.61%

Welcome to the ToolWeaver documentation! This guide is organized by audience and use case.

## 🎯 Project Status & Quick Links

**NEW:** [Phases Overview](PHASES_OVERVIEW.md) - What was implemented in Phases 0-4  
**NEW:** [Examples Guide](examples/) - 29 runnable examples  
**NEW:** [Examples Testing Guide](examples/EXAMPLES_TESTING_GUIDE.md) - How to test examples

---

## 🧭 Quick Navigation

**👤 New User?** → Start with [Getting Started](#-getting-started)  
**👨‍💻 Contributing?** → See [Developer Guide](#-developer-guide)  
**🚀 Deploying?** → Check [Deployment](#-deployment)  
**📚 Deep Dive?** → Browse [Reference](#-reference)  
**🧪 Learning?** → Explore [29 Examples](examples/)

---

## 👤 Getting Started

*For users installing ToolWeaver via `pip install toolweaver`*

| Document | Description | Time |
|----------|-------------|------|
| [Quick Reference](getting-started/quickstart.md) | 5-minute quick start | 5 min |
| [Discovering Tools](getting-started/discovering-tools.md) | Find and explore tools | 10 min |
| [Registering Tools](getting-started/registering-tools.md) | Add your own tools | 10 min |
| [Extending ToolWeaver](getting-started/extending.md) | Custom plugins and tools | 15 min |
| [FAQ](getting-started/faq.md) | Common questions | 10 min |

**Also See:**
- [User Guide](user-guide/GETTING_STARTED.md) - Complete feature guide
- [Configuration](user-guide/CONFIGURATION.md) - Setup all providers
- [Troubleshooting](user-guide/TROUBLESHOOTING.md) - Common issues

**Start here:** [Quick Reference](getting-started/quickstart.md)

---

## 👨‍💻 Developer Guide

*For contributors modifying ToolWeaver source code*

| Document | Description | Time |
|----------|-------------|------|
| [Phases Overview](PHASES_OVERVIEW.md) | What was implemented | 10 min |
| [Architecture](developer-guide/ARCHITECTURE.md) | System design and components | 30 min |
| [Implementation](developer-guide/IMPLEMENTATION.md) | Code structure and patterns | 20 min |
| [Security](developer-guide/SECURITY.md) | Security model and sandboxing | 15 min |
| [Workflow](developer-guide/WORKFLOW.md) | Development workflow and setup | 15 min |
| [Publishing](developer-guide/PUBLISHING.md) | Package release process | 10 min |

**Prerequisites:**
- Read [../CONTRIBUTING.md](../CONTRIBUTING.md) first
- Setup: `git clone` + `pip install -e ".[dev]"`
- Explore: [29 Examples](examples/)

**Start here:** [Phases Overview](PHASES_OVERVIEW.md)

---

## 🧪 Examples

*29 runnable examples demonstrating all major features*

| Category | Count | Purpose |
|----------|-------|---------|
| [Basic Usage](examples/#-basic-usage-start-here) | 3 | Getting started |
| [Tool Integration](examples/#-tool-integration--discovery) | 3 | Tool discovery & catalogs |
| [Workflows](examples/#-workflow--composition) | 3 | Tool composition & chaining |
| [Advanced Patterns](examples/#-advanced-patterns) | 3 | Monitoring, caching, routing |
| [Agent Patterns](examples/#-agent-patterns) | 6 | Agent dispatch & coordination |
| [Specialized Workflows](examples/#-specialized-workflows) | 5 | Complete pipelines, approvals |
| [Distributed & Parallel](examples/#-distributed--parallel) | 2 | Parallel execution |
| [Advanced Integration](examples/#-advanced-integration) | 2 | MCP, cost optimization |
| [Templates](examples/#-templates--learning) | 2 | Community templates |

**Total:** 29 examples | All documented | All ready to run

**Start here:** [Examples Overview](examples/README.md)

---

## 🚀 Deployment

*Production deployment guides*

| Document | Purpose |
|----------|---------|
| [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md) | Deploy to production |
| [Azure Setup](deployment/AZURE_SETUP.md) | Azure OpenAI configuration |
| [Redis Setup](deployment/REDIS_SETUP.md) | Redis for caching |
| [Qdrant Setup](deployment/QDRANT_SETUP.md) | Vector DB setup |
| [SQLite + Grafana](deployment/SQLITE_GRAFANA_SETUP.md) | Monitoring setup |

**Start here:** [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md)

---

## 📚 Reference

*Detailed technical reference*

| Document | Purpose |
|----------|---------|
| [Two-Model Architecture](reference/TWO_MODEL_ARCHITECTURE.md) | Large + small model design |
| [Workflow Architecture](reference/WORKFLOW_ARCHITECTURE.md) | Workflow execution model |
| [Registry Discovery](reference/REGISTRY_DISCOVERY.md) | Tool discovery mechanisms |
| [Search Tuning](reference/SEARCH_TUNING.md) | Optimize tool search |
| [Prompt Caching](reference/PROMPT_CACHING.md) | Cache prompts for speed |
| [Migration Guide](reference/MIGRATION_GUIDE.md) | Upgrade between versions |
| [Analytics Guide](reference/ANALYTICS_GUIDE.md) | Monitoring and metrics |
| [Small Model Improvements](reference/SMALL_MODEL_IMPROVEMENTS.md) | Ollama phi3 enhancements |
| [Skill Library](reference/SKILL_LIBRARY.md) | Skill management reference |

**Start here:** [Two-Model Architecture](reference/TWO_MODEL_ARCHITECTURE.md)

---

## 🔐 Security

| Document | Purpose |
|----------|---------|
| [Threat Model](security/threat-model.md) | Security analysis and threats |

---

## 🎓 How It Works

*Progressive depth explanations*

| Document | Purpose | Depth |
|----------|---------|-------|
| [README](how-it-works/README.md) | Overview | Overview |
| [Programmatic Tool Calling](how-it-works/programmatic-tool-calling/README.md) | How tools are called | Technical |
| [Detailed Explanation](how-it-works/programmatic-tool-calling/EXPLAINED.md) | Deep dive | Very technical |
| [Integration Summary](how-it-works/programmatic-tool-calling/INTEGRATION_SUMMARY.md) | Implementation summary | Technical |
| [Walkthrough](how-it-works/programmatic-tool-calling/WALKTHROUGH.md) | Step-by-step | Tutorial |
| [Reference](how-it-works/programmatic-tool-calling/REFERENCE.md) | API reference | Reference |
| [Diagrams](how-it-works/programmatic-tool-calling/DIAGRAMS.md) | Architecture diagrams | Visual |

**Start here:** [How It Works Overview](how-it-works/README.md)

---

## 📁 Internal Documentation

*Private team documentation (not in public docs)*

- [Phases Overview](PHASES_OVERVIEW.md) - What was completed
- [Internal Docs](internal/) - Strategic, planning, release notes
- [Test Reports](internal/test-reports/) - Coverage and failure analysis

---

## 🗂️ Documentation Structure

```
docs/
├── README.md (this file - navigation hub)
├── PHASES_OVERVIEW.md (what was implemented)
├── examples/ (29 runnable examples)
├── getting-started/ (for new users)
├── user-guide/ (features and usage)
├── developer-guide/ (for contributors)
├── deployment/ (production setup)
├── reference/ (technical reference)
├── how-it-works/ (progressive explanations)
├── architecture/ (system design)
├── security/ (threat model)
└── internal/ (strategic & planning)
```

---

## 🎯 Common Tasks

### I want to...

**Use ToolWeaver as a package:**
→ [Getting Started](user-guide/GETTING_STARTED.md)

**Contribute to ToolWeaver:**
→ [Architecture](developer-guide/ARCHITECTURE.md)

**Deploy to production:**
→ [Production Deployment](deployment/PRODUCTION_DEPLOYMENT.md)

**Learn about implementation:**
→ [Phases Overview](PHASES_OVERVIEW.md)

**Run examples:**
→ [Examples Guide](examples/README.md)

**Test examples:**
→ [Examples Testing Guide](examples/EXAMPLES_TESTING_GUIDE.md)

**Understand security:**
→ [Security Guide](developer-guide/SECURITY.md) or [Threat Model](security/threat-model.md)

**Optimize costs:**
→ [Cost-Aware Selection](user-guide/cost_aware_selection.md)

---

## 📊 Documentation Statistics

| Metric | Value |
|--------|-------|
| Total Documents | 75+ markdown files |
| Examples | 29 runnable |
| Coverage | 67.61% code coverage |
| Tests | 971/985 passing (98.6%) |
| Phases Complete | 5 (0-4) |
| Features | 30+ major |

---

## 🔗 Navigation Tips

- **Use Ctrl+F** to search within this page
- **Follow the blue links** to go deeper
- **Return to index** via breadcrumb links
- **Check "Start here" links** for first-time guidance
- **Review related docs** at the bottom of each page

---

**Last Updated:** December 23, 2025  
**Version:** 0.6.0

---

## 👨‍💻 Developer Guide

*For contributors modifying ToolWeaver source code*

| Document | Description | Time |
|----------|-------------|------|
| [Architecture](developer-guide/ARCHITECTURE.md) | System design and components | 30 min |
| [Implementation](developer-guide/IMPLEMENTATION.md) | Code structure and patterns | 20 min |
| [Security](developer-guide/SECURITY.md) | Security model and sandboxing | 15 min |
| [Code Validation](developer-guide/CODE_VALIDATION.md) | Optional validation for generated code | 10 min |
| [Executing Skills](developer-guide/EXECUTING_SKILLS.md) | Run saved code snippets from Orchestrator | 10 min |
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
| [Analytics Guide](reference/ANALYTICS_GUIDE.md) | Complete tri-backend guide (SQLite, OTLP, Prometheus) | All |
| [Two-Model Architecture](reference/TWO_MODEL_ARCHITECTURE.md) | Large + small model design | Advanced |
| [Workflow Architecture](reference/WORKFLOW_ARCHITECTURE.md) | Workflow engine internals | Advanced |
| [Prompt Caching](reference/PROMPT_CACHING.md) | Cost optimization techniques | All |
| [Search Tuning](reference/SEARCH_TUNING.md) | Optimize tool search | Advanced |
| [Migration Guide](reference/MIGRATION_GUIDE.md) | Upgrade between versions | All |
| [Small Model Improvements](reference/SMALL_MODEL_IMPROVEMENTS.md) | Enhance small models | Advanced |
| [Skill Library](reference/SKILL_LIBRARY.md) | Save and reuse generated code | Advanced |
| [Registry Discovery](reference/REGISTRY_DISCOVERY.md) | External MCP registry integration | Advanced |

---

## 📖 Additional Resources

### Samples & Examples
- [samples/](../samples/) - Ready-to-run examples using installed package
- [examples/](../examples/) - Development examples using source code
- [examples/README.md](../examples/README.md) - Index including new advanced flows 19–21 (hybrid tool↔agent, approval gate, error recovery); 19–21 use stubbed smoke tests.

### Performance Benchmarks (Scope)
- We run a regression-focused benchmark suite to ensure discovery, search, and orchestration stay within our targets.
- It is **not** a vendor or “vanilla vs optimized” comparison; results are environment-specific.
- For A/B baselines, run the suite on both builds (same hardware/load) and compare p50/p95 and resource usage.

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
    ├── ANALYTICS_GUIDE.md            # Tri-backend analytics (SQLite, OTLP, Prometheus)
    ├── TWO_MODEL_ARCHITECTURE.md     # Design patterns
    ├── WORKFLOW_ARCHITECTURE.md      # Internals
    ├── PROMPT_CACHING.md             # Optimization
    ├── SEARCH_TUNING.md              # Tuning guide
    ├── MIGRATION_GUIDE.md            # Upgrades
    ├── SMALL_MODEL_IMPROVEMENTS.md   # Enhancements
    ├── SKILL_LIBRARY.md              # Reusable code skills
    └── REGISTRY_DISCOVERY.md         # External registry integration
```

---

## 🎯 Learning Paths

### Path 1: Quick Start (New User)
1. [Getting Started](user-guide/GETTING_STARTED.md) - 10 min
2. [Configuration](user-guide/CONFIGURATION.md) - 15 min
3. [Features Guide](user-guide/FEATURES_GUIDE.md) - Overview - 10 min
4. Try [examples/01-basic-receipt-processing](../examples/01-basic-receipt-processing/)

### Path 2: Tools Deep Dive (Deterministic Operations)
1. [Features Guide](user-guide/FEATURES_GUIDE.md) - Read "Discovery Systems" section
2. [MCP Tools Guide](user-guide/MCP_SETUP_GUIDE.md) - 15 min
3. [Features Guide](user-guide/FEATURES_GUIDE.md) - Read "Execution Paradigms" section
4. Try [examples/02-receipt-with-categorization](../examples/02-receipt-with-categorization/)

### Path 3: Agents Deep Dive (Complex Reasoning)
1. [Features Guide](user-guide/FEATURES_GUIDE.md) - Read "Discovery Systems" section
2. [A2A Agents Guide](user-guide/A2A_SETUP_GUIDE.md) - 20 min
3. [Features Guide](user-guide/FEATURES_GUIDE.md) - Read "Execution Paradigms" section
4. Try [examples/16-agent-delegation](../examples/16-agent-delegation/)

### Path 4: Hybrid Workflows (Tools + Agents)
1. Complete Path 2 + Path 3
2. [Workflow Usage Guide](user-guide/WORKFLOW_USAGE_GUIDE.md) - 20 min
3. Try [examples/17-multi-agent-coordination](../examples/17-multi-agent-coordination/)
4. Try [examples/18-tool-agent-hybrid](../examples/18-tool-agent-hybrid/)

### Path 5: Deep Understanding (Architecture)
1. [Features Guide](user-guide/FEATURES_GUIDE.md) - Full read - 30 min
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

**Last Updated:** December 18, 2025  
**Version:** 0.1.3
