# How to Aggregate Agent Results

Step-by-step guide to combine results from multiple parallel agents for consensus, voting, or best-answer selection.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [Multi-Agent Coordination](../reference/deep-dives/multi-agent-coordination.md)
- Familiarity with [Agent Delegation](../tutorials/agent-delegation.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Parallel agent execution  
✅ Result aggregation strategies (consensus, voting, best-of-N)  
✅ Conflict resolution logic  
✅ Quality scoring for agent outputs  
✅ Complete multi-agent coordination pipeline  

**Estimated time:** 25 minutes

---

## Step 1: Execute Agents in Parallel

### 1.1 Basic Parallel Execution

```python
import asyncio
from orchestrator.a2a.client import A2AClient

async def execute_agents_parallel(task: dict, agent_ids: list):
    """Execute multiple agents in parallel on same task."""
    
    client = A2AClient(config_path="agents.yaml")
    
    # Create tasks for all agents
    tasks = [
        client.delegate(
            agent_id=agent_id,
            request=task,
            idempotency_key=f"{agent_id}-{task['id']}"
        )
        for agent_id in agent_ids
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

# Usage
task = {"query": "Analyze Q4 revenue trends", "id": "task-123"}
agent_ids = ["analyst_1", "analyst_2", "analyst_3"]

results = await execute_agents_parallel(task, agent_ids)
```

---

## Step 2: Consensus Aggregation

### 2.1 Majority Voting

```python
from collections import Counter

def aggregate_by_voting(results: list, extract_answer_fn):
    """Select answer by majority vote."""
    
    # Extract answers from results
    answers = [extract_answer_fn(r) for r in results if not isinstance(r, Exception)]
    
    if not answers:
        raise ValueError("No valid answers from agents")
    
    # Count votes
    vote_counts = Counter(answers)
    
    # Get majority answer
    winner, votes = vote_counts.most_common(1)[0]
    confidence = votes / len(answers)
    
    return {
        "answer": winner,
        "confidence": confidence,
        "votes": dict(vote_counts),
        "total_agents": len(answers)
    }

# Usage
def extract_risk_level(result):
    \"\"\"Extract risk level from agent response.\"\"\"
    return result.get("risk_level", "unknown")

# Get consensus
consensus = aggregate_by_voting(results, extract_risk_level)
print(f"Consensus: {consensus['answer']} ({consensus['confidence']:.0%} agreement)")
# Output: Consensus: medium (67% agreement)
```

### 2.2 Weighted Voting

```python
def aggregate_by_weighted_voting(results: list, agent_weights: dict):
    """Weight votes by agent reliability."""
    
    vote_scores = {}
    
    for agent_id, result in zip(agent_ids, results):
        if isinstance(result, Exception):
            continue
        
        answer = result.get("risk_level")
        weight = agent_weights.get(agent_id, 1.0)
        
        vote_scores[answer] = vote_scores.get(answer, 0.0) + weight
    
    # Select answer with highest weighted score
    winner = max(vote_scores, key=vote_scores.get)
    total_weight = sum(vote_scores.values())
    confidence = vote_scores[winner] / total_weight
    
    return {
        "answer": winner,
        "confidence": confidence,
        "weighted_scores": vote_scores
    }

# Usage with agent reliability weights
agent_weights = {
    "analyst_1": 1.5,  # 50% more weight (more reliable)
    "analyst_2": 1.0,  # Standard weight
    "analyst_3": 0.8   # 20% less weight (less reliable)
}

consensus = aggregate_by_weighted_voting(results, agent_weights)
```

---

## Step 3: Best-of-N Selection

### 3.1 Score-Based Selection

```python
def select_best_result(results: list, scoring_fn):
    """Select best result based on quality score."""
    
    scored_results = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        
        score = scoring_fn(result)
        scored_results.append({
            "agent_index": i,
            "result": result,
            "score": score
        })
    
    if not scored_results:
        raise ValueError("No valid results to score")
    
    # Sort by score (descending)
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_results[0]

# Usage
def score_analysis(result: dict) -> float:
    \"\"\"Score analysis based on completeness and confidence.\"\"\"
    
    score = 0.0
    
    # Completeness (0-50 points)
    if "summary" in result:
        score += 20
    if "recommendations" in result:
        score += 20
    if "data_points" in result:
        score += 10
    
    # Confidence (0-50 points)
    confidence = result.get("confidence", 0.0)
    score += confidence * 50
    
    return score

best = select_best_result(results, score_analysis)
print(f"Best result from agent {best['agent_index']} (score: {best['score']:.1f})")
```

### 3.2 Multi-Criteria Selection

```python
def select_best_multicriteria(results: list, criteria_weights: dict):
    """Select best result using multiple weighted criteria."""
    
    def score_result(result: dict) -> float:
        total_score = 0.0
        
        # Criterion 1: Completeness
        completeness = len(result.get("sections", [])) / 5.0  # Normalize to 0-1
        total_score += completeness * criteria_weights.get("completeness", 0.3)
        
        # Criterion 2: Confidence
        confidence = result.get("confidence", 0.0)
        total_score += confidence * criteria_weights.get("confidence", 0.3)
        
        # Criterion 3: Detail level
        detail = len(result.get("details", "")) / 1000.0  # Normalize
        total_score += min(detail, 1.0) * criteria_weights.get("detail", 0.2)
        
        # Criterion 4: Response time (favor faster)
        latency = result.get("latency", 10.0)
        speed_score = max(0, 1.0 - (latency / 30.0))  # 30s = 0 score
        total_score += speed_score * criteria_weights.get("speed", 0.2)
        
        return total_score
    
    best = select_best_result(results, score_result)
    return best

# Usage
criteria_weights = {
    "completeness": 0.4,  # 40%
    "confidence": 0.3,    # 30%
    "detail": 0.2,        # 20%
    "speed": 0.1          # 10%
}

best = select_best_multicriteria(results, criteria_weights)
```

---

## Step 4: Ensemble Aggregation

### 4.1 Average Numerical Results

```python
import statistics

def aggregate_numerical_results(results: list, field: str):
    """Average numerical predictions from multiple agents."""
    
    values = []
    
    for result in results:
        if isinstance(result, Exception):
            continue
        
        value = result.get(field)
        if value is not None and isinstance(value, (int, float)):
            values.append(value)
    
    if not values:
        raise ValueError(f"No valid numerical values for field '{field}'")
    
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
        "count": len(values),
        "individual_values": values
    }

# Usage - aggregate revenue predictions
task = {"query": "Predict Q1 2026 revenue"}
results = await execute_agents_parallel(task, ["forecaster_1", "forecaster_2", "forecaster_3"])

aggregated = aggregate_numerical_results(results, "predicted_revenue")
print(f"Revenue prediction: ${aggregated['mean']:,.0f} ± ${aggregated['stdev']:,.0f}")
print(f"Range: ${aggregated['min']:,.0f} - ${aggregated['max']:,.0f}")
```

### 4.2 Merge Text Responses

```python
def merge_text_responses(results: list, max_length: int = 500):
    """Merge text responses from multiple agents."""
    
    texts = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        
        text = result.get("response", "")
        if text:
            texts.append(f"Agent {i+1}: {text}")
    
    # Combine with separators
    merged = "\n\n".join(texts)
    
    # Truncate if too long
    if len(merged) > max_length:
        merged = merged[:max_length] + "..."
    
    return {
        "merged_text": merged,
        "source_count": len(texts),
        "total_length": len(merged)
    }

# Usage
merged = merge_text_responses(results, max_length=1000)
print(merged["merged_text"])
```

---

## Step 5: Conflict Resolution

### 5.1 Detect Conflicts

```python
def detect_conflicts(results: list, extract_answer_fn):
    """Detect when agents disagree significantly."""
    
    answers = [extract_answer_fn(r) for r in results if not isinstance(r, Exception)]
    
    if not answers:
        return {"has_conflict": False}
    
    # Count unique answers
    unique_answers = set(answers)
    
    # Check if unanimous
    if len(unique_answers) == 1:
        return {
            "has_conflict": False,
            "unanimous": True,
            "answer": list(unique_answers)[0]
        }
    
    # Check vote distribution
    vote_counts = Counter(answers)
    winner, winner_votes = vote_counts.most_common(1)[0]
    confidence = winner_votes / len(answers)
    
    # Flag as conflict if no clear majority (< 60%)
    has_conflict = confidence < 0.6
    
    return {
        "has_conflict": has_conflict,
        "unanimous": False,
        "confidence": confidence,
        "winner": winner,
        "vote_distribution": dict(vote_counts),
        "conflict_severity": 1.0 - confidence
    }

# Usage
conflict_info = detect_conflicts(results, extract_risk_level)

if conflict_info["has_conflict"]:
    print(f"⚠️  Conflict detected (severity: {conflict_info['conflict_severity']:.0%})")
    print(f"Vote distribution: {conflict_info['vote_distribution']}")
```

### 5.2 Resolve with Tiebreaker Agent

```python
async def resolve_conflict_with_tiebreaker(results: list, tiebreaker_agent: str):
    """Use a tiebreaker agent when results conflict."""
    
    # Check for conflict
    conflict_info = detect_conflicts(results, extract_risk_level)
    
    if not conflict_info["has_conflict"]:
        # No conflict, return winner
        return conflict_info["winner"]
    
    # Call tiebreaker agent with all results
    client = A2AClient(config_path="agents.yaml")
    
    tiebreaker_result = await client.delegate(
        agent_id=tiebreaker_agent,
        request={
            "task": "resolve_conflict",
            "agent_results": [r for r in results if not isinstance(r, Exception)],
            "conflict_info": conflict_info
        }
    )
    
    return tiebreaker_result.get("resolution")

# Usage
if conflict_info["has_conflict"]:
    resolution = await resolve_conflict_with_tiebreaker(results, "senior_analyst")
    print(f"Tiebreaker resolution: {resolution}")
```

---

## Step 6: Real-World Example

Complete multi-agent analysis with aggregation.

**File:** `pipeline/multi_agent_analysis.py`

```python
import asyncio
from orchestrator.a2a.client import A2AClient

class MultiAgentAnalyzer:
    def __init__(self):
        self.client = A2AClient(config_path="agents.yaml")
        self.agent_weights = {
            "analyst_senior": 1.5,
            "analyst_mid": 1.0,
            "analyst_junior": 0.7
        }
    
    async def analyze_with_consensus(self, company_id: str):
        """Analyze company using multiple agents, aggregate results."""
        
        # Step 1: Parallel agent execution
        print("Step 1: Executing parallel analysis...")
        
        agents = ["analyst_senior", "analyst_mid", "analyst_junior"]
        task = {
            "company_id": company_id,
            "analysis_type": "financial_health"
        }
        
        results = await asyncio.gather(*[
            self.client.delegate(
                agent_id=agent_id,
                request=task,
                idempotency_key=f"{agent_id}-{company_id}"
            )
            for agent_id in agents
        ], return_exceptions=True)
        
        # Step 2: Check for conflicts
        print("Step 2: Checking for conflicts...")
        
        conflict_info = detect_conflicts(
            results,
            lambda r: r.get("risk_rating")
        )
        
        if conflict_info["has_conflict"]:
            print(f"⚠️  Conflict detected ({conflict_info['conflict_severity']:.0%} disagreement)")
            
            # Use weighted voting for resolution
            consensus = aggregate_by_weighted_voting(results, self.agent_weights)
        else:
            print("✓ Agents in agreement")
            consensus = {"answer": conflict_info["winner"], "confidence": 1.0}
        
        # Step 3: Aggregate numerical predictions
        print("Step 3: Aggregating predictions...")
        
        revenue_pred = aggregate_numerical_results(results, "revenue_forecast")
        
        # Step 4: Select best detailed analysis
        print("Step 4: Selecting best detailed analysis...")
        
        def score_detail(result):
            return (
                len(result.get("recommendations", [])) * 10 +
                result.get("confidence", 0) * 50
            )
        
        best_detail = select_best_result(results, score_detail)
        
        # Step 5: Compile final report
        return {
            "risk_rating": consensus["answer"],
            "risk_confidence": consensus["confidence"],
            "revenue_forecast": {
                "mean": revenue_pred["mean"],
                "range": (revenue_pred["min"], revenue_pred["max"])
            },
            "detailed_analysis": best_detail["result"],
            "conflict_detected": conflict_info["has_conflict"]
        }

# Usage
analyzer = MultiAgentAnalyzer()
report = await analyzer.analyze_with_consensus("AAPL")

print(f"Risk Rating: {report['risk_rating']} ({report['risk_confidence']:.0%} confidence)")
print(f"Revenue Forecast: ${report['revenue_forecast']['mean']:,.0f}")
```

---

## Verification

Test your aggregation logic:

```python
async def verify_aggregation():
    """Verify aggregation strategies."""
    
    # Mock results
    results = [
        {"risk_level": "medium", "confidence": 0.85, "revenue_forecast": 1000000},
        {"risk_level": "medium", "confidence": 0.90, "revenue_forecast": 1100000},
        {"risk_level": "low", "confidence": 0.75, "revenue_forecast": 950000}
    ]
    
    # Test 1: Voting
    consensus = aggregate_by_voting(results, lambda r: r["risk_level"])
    assert consensus["answer"] == "medium", "Voting failed"
    assert consensus["confidence"] == 2/3, "Confidence calculation failed"
    print("✓ Voting aggregation working")
    
    # Test 2: Numerical aggregation
    agg = aggregate_numerical_results(results, "revenue_forecast")
    assert 950000 <= agg["mean"] <= 1100000, "Mean out of range"
    print("✓ Numerical aggregation working")
    
    # Test 3: Best selection
    best = select_best_result(results, lambda r: r["confidence"])
    assert best["result"]["confidence"] == 0.90, "Best selection failed"
    print("✓ Best-of-N selection working")
    
    print("\n✅ All checks passed!")

await verify_aggregation()
```

---

## Common Issues

### Issue 1: All Agents Fail

**Symptom:** No valid results to aggregate

**Solution:** Implement graceful degradation

```python
results = await execute_agents_parallel(task, agent_ids)
valid_results = [r for r in results if not isinstance(r, Exception)]

if not valid_results:
    # Fallback to single reliable agent
    return await client.delegate(agent_id="fallback_agent", request=task)
```

### Issue 2: Tie in Voting

**Symptom:** Equal votes for multiple answers

**Solution:** Use weighted voting or tiebreaker

```python
vote_counts = Counter(answers)
top_votes = vote_counts.most_common(2)

if len(top_votes) > 1 and top_votes[0][1] == top_votes[1][1]:
    # Tie detected, use tiebreaker
    return await resolve_conflict_with_tiebreaker(results, "tiebreaker_agent")
```

### Issue 3: Outlier Results

**Symptom:** One agent returns wildly different value

**Solution:** Filter outliers using standard deviation

```python
import statistics

def filter_outliers(values: list, std_threshold: float = 2.0):
    \"\"\"Remove values more than N standard deviations from mean.\"\"\"
    
    if len(values) < 3:
        return values
    
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    
    filtered = [
        v for v in values
        if abs(v - mean) <= std_threshold * stdev
    ]
    
    return filtered if filtered else values  # Return original if all filtered
```

---

## Next Steps

- **Deep Dive:** [Multi-Agent Coordination](../reference/deep-dives/multi-agent-coordination.md) - Advanced patterns
- **Tutorial:** [Agent Delegation](../tutorials/agent-delegation.md) - Learn delegation basics
- **Sample:** [17-multi-agent-coordination](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/17-multi-agent-coordination) - Complete example

## Related Guides

- [Configure A2A Agents](configure-a2a-agents.md) - Set up agents
- [Implement Retry Logic](implement-retry-logic.md) - Handle agent failures
- [Monitor Performance](monitor-performance.md) - Track multi-agent metrics
