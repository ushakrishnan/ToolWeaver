# ToolWeaver Examples

Complete guide to 29 runnable examples demonstrating all major ToolWeaver features.

**Total Examples:** 29  
**Setup Status:** ✅ All configured with .env and requirements.txt  
**Test Coverage:** All examples ready for integration testing

---

## 🚀 Quick Start

```bash
cd examples/01-basic-receipt-processing
pip install -r requirements.txt
python process_receipt.py
```

---

## 📚 Examples by Category

### Basic Usage (Start Here)
1. **[01-basic-receipt-processing](../../examples/01-basic-receipt-processing)** - Simple OCR & receipt processing with Azure CV
2. **[02-receipt-with-categorization](../../examples/02-receipt-with-categorization)** - Receipt processing with LLM-based categorization
3. **[09-code-execution](../../examples/09-code-execution)** - Execute generated code safely

### Tool Integration & Discovery
4. **[03-github-operations](../../examples/03-github-operations)** - GitHub MCP tools for repos, issues, PRs
5. **[04-vector-search-discovery](../../examples/04-vector-search-discovery)** - Vector search + embedding-based tool discovery
6. **[12-sharded-catalog](../../examples/12-sharded-catalog)** - Tool catalog with sharding for scale

### Workflow & Composition
7. **[05-workflow-library](../../examples/05-workflow-library)** - Build and manage workflow collections
8. **[23-adding-new-tools](../../examples/23-adding-new-tools)** - Add custom tools to orchestrator
9. **[15-control-flow](../../examples/15-control-flow)** - Conditional execution and branching

### Advanced Patterns
10. **[06-monitoring-observability](../../examples/06-monitoring-observability)** - Monitoring, tracing, metrics
11. **[07-caching-optimization](../../examples/07-caching-optimization)** - Response caching strategies
12. **[08-hybrid-model-routing](../../examples/08-hybrid-model-routing)** - Route tasks to different LLMs based on cost

### Agent Patterns
13. **[10-multi-step-planning](../../examples/10-multi-step-planning)** - Multi-step execution planning
14. **[11-programmatic-executor](../../examples/11-programmatic-executor)** - Programmatic orchestrator execution
15. **[14-programmatic-execution](../../examples/14-programmatic-execution)** - Alternative programmatic approach
16. **[16-agent-delegation](../../examples/16-agent-delegation)** - Delegate work to sub-agents
17. **[17-multi-agent-coordination](../../examples/17-multi-agent-coordination)** - Coordinate multiple agents
18. **[18-tool-agent-hybrid](../../examples/18-tool-agent-hybrid)** - Hybrid tool and agent execution

### Specialized Workflows
19. **[13-complete-pipeline](../../examples/13-complete-pipeline)** - End-to-end complete pipeline
20. **[19-fetch-analyze-store](../../examples/19-fetch-analyze-store)** - Fetch data, analyze, store results
21. **[20-approval-workflow](../../examples/20-approval-workflow)** - Multi-step approval workflows
22. **[21-error-recovery](../../examples/21-error-recovery)** - Error handling and recovery patterns
23. **[22-end-to-end-showcase](../../examples/22-end-to-end-showcase)** - Comprehensive feature showcase

### Distributed & Parallel
24. **[25-parallel-agents](../../examples/25-parallel-agents)** - Run multiple agents in parallel
25. **[28-quicksort-orchestration](../../examples/28-quicksort-orchestration)** - Parallel algorithm orchestration

### Advanced Integration
26. **[24-external-mcp-adapter](../../examples/24-external-mcp-adapter)** - Integrate external MCP servers
27. **[27-cost-optimization](../../examples/27-cost-optimization)** - Cost-aware model and tool selection

### Templates & Learning
28. **[community-plugin-template](../../examples/community-plugin-template)** - Template for creating plugins
29. **[legacy-demos](../../examples/legacy-demos)** - Legacy examples and demos

---

## 🔧 Example Setup

Each example includes:
- ✅ `README.md` - Feature documentation
- ✅ `requirements.txt` - Dependencies (smart-loaded with only needed packages)
- ✅ `.env.example` - Configuration template
- ✅ `.env` - Auto-populated with values from root `.env`
- ✅ Python source files - Runnable code

### Environment Configuration

Copy your API keys to each example's `.env`:

```bash
# Option 1: Automatic (already done)
cd examples/01-basic-receipt-processing
# .env already populated from root .env

# Option 2: Manual
cp /path/to/root/.env examples/EXAMPLE_NAME/.env
```

**Required Keys Depend on Example:**
- Azure examples: `AZURE_OPENAI_*`, `AZURE_CV_*`
- GitHub examples: `GITHUB_TOKEN`
- All examples: `OPENAI_API_KEY` (or alternative LLM)
- Cache examples: `REDIS_URL`
- Advanced examples: `OLLAMA_HOST`

---

## 🧪 Testing Examples

### Run Single Example
```bash
cd examples/01-basic-receipt-processing
python process_receipt.py
```

### Run All Examples (Batch Test)
```bash
# Use the test script (creates if needed)
python examples/test_all_examples.py
```

### Integration Testing
See [EXAMPLES_TESTING_GUIDE.md](EXAMPLES_TESTING_GUIDE.md) for detailed testing strategies.

---

## 📖 Learning Path

**Beginner → Intermediate → Advanced**

1. Start: [01-basic-receipt-processing](../../examples/01-basic-receipt-processing)
2. Try: [02-receipt-with-categorization](../../examples/02-receipt-with-categorization)
3. Explore: [03-github-operations](../../examples/03-github-operations)
4. Learn workflows: [05-workflow-library](../../examples/05-workflow-library)
5. Advanced: [10-multi-step-planning](../../examples/10-multi-step-planning)
6. Showcase: [22-end-to-end-showcase](../../examples/22-end-to-end-showcase)

---

## 🤝 Extending Examples

To create your own example:

1. **Copy template:** `cp -r examples/community-plugin-template examples/my-example`
2. **Update files:**
   - `README.md` - Your example documentation
   - `requirements.txt` - Your dependencies
   - `.env.example` - Your configuration keys
   - Python files - Your implementation
3. **Test locally:** `python examples/my-example/main.py`
4. **Contribute:** Submit PR with example

---

## 📊 Example Statistics

| Metric | Value |
|--------|-------|
| Total Examples | 29 |
| Lines of Code | ~3,500+ |
| Documented | ✅ 100% |
| With .env | ✅ 100% |
| With requirements.txt | ✅ 100% |
| Runnable | ✅ Ready after setup |

---

## 🔗 Related Documentation

- [Getting Started](../for-package-users/quickstart.md) - New user setup
- [User Guide](../user-guide/GETTING_STARTED.md) - Feature documentation
- [Developer Guide](../developer-guide/ARCHITECTURE.md) - For contributors
- [Deployment](../deployment/PRODUCTION_DEPLOYMENT.md) - Production setup

