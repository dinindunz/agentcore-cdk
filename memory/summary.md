# Summary Memory

## What It Is

Summary memory automatically **condenses conversations into concise summaries**, extracting key points, decisions, and outcomes from sessions. It enables quick recaps of previous interactions without reviewing full conversation history.

**Key Characteristics:**
- ✅ **Session-scoped** - Summarises specific conversation sessions
- ✅ **Condensed format** - High-level overview, not verbatim
- ✅ **Key point extraction** - Highlights important decisions and outcomes
- ✅ **Cross-session retrieval** - Access summaries from past sessions
- ✅ **60+ second extraction** - Asynchronous processing from short-term events

## When to Use

Use summary memory for:
- ✅ **Session recaps** - "What did we discuss last week?"
- ✅ **Quick context** - Understand session without reading full history
- ✅ **Decision tracking** - "What was decided in the previous meeting?"
- ✅ **Onboarding** - Catch up on past interactions
- ✅ **Multi-session workflows** - Reference earlier session outcomes

## Agent Code Implementation

### Memory Client

```python
from typing import List, Dict, Optional
import boto3


class SummaryMemory:
    """Manages session summaries for quick context retrieval."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def retrieve_session_summary(
        self,
        actor_id: str,
        session_id: str,
        query: Optional[str] = None,
        top_k: int = 1,
    ) -> List[Dict]:
        """
        Retrieve summary for a specific session.

        Args:
            actor_id: User identifier
            session_id: Session identifier
            query: Optional semantic query to filter summary
            top_k: Number of summary records to return

        Returns:
            List of summary records for the session
        """
        search_criteria = {"searchQuery": query} if query else {}

        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/summaries/actors/{actor_id}/sessions/{session_id}/",
            searchCriteria=search_criteria,
            maxResults=top_k
        )
        return response.get('memoryRecordSummaries', [])

    def retrieve_recent_summaries(
        self,
        actor_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve summaries across multiple sessions using semantic search.

        Args:
            actor_id: User identifier
            query: Semantic query to find relevant summaries
            top_k: Number of summaries to return

        Returns:
            List of relevant session summaries
        """
        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/summaries/actors/{actor_id}/",
            searchCriteria={"searchQuery": query},
            maxResults=top_k
        )
        return response.get('memoryRecordSummaries', [])
```

### Integration with Agent

```python
# src/agent/main.py
from summary_memory import SummaryMemory

summaries = SummaryMemory(
    memory_id=os.environ["MEMORY_ID"],
    region_name=os.environ["REGION_NAME"]
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", f"session_{uuid.uuid4()}")

    # 1. Check if user is referencing past sessions
    if any(keyword in user_message.lower() for keyword in ["last time", "previously", "earlier session"]):
        # Query past summaries
        past_summaries = summaries.retrieve_recent_summaries(
            actor_id=actor_id,
            query=user_message,
            top_k=3
        )

        if past_summaries:
            summary_context = "\n\n## Previous Session Summaries:\n"
            for summary in past_summaries:
                summary_context += f"- {summary.get('value', '')}\n"

            # Enhance prompt with past context
            user_message = f"{summary_context}\n## Current Request:\n{user_message}"

    # 2. Execute agent
    result = agent(user_message)
    response_text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )

    return {"result": response_text}

    # Note: Summary extracted automatically after session events (60+ sec delay)
```

## Namespace Pattern

### Session-Level Summaries
```
/strategies/summaries/actors/{actorId}/sessions/{sessionId}/
```
**Use for**: Summaries of specific sessions

```
/strategies/summaries/actors/user-sarah-123/sessions/session-2024-01-15-001/summary
/strategies/summaries/actors/user-sarah-123/sessions/session-2024-01-16-002/summary
/strategies/summaries/actors/user-sarah-123/sessions/session-2024-01-20-005/summary
```

### Actor-Level (Cross-Session) Queries
```
/strategies/summaries/actors/{actorId}/
```
**Use for**: Semantic search across all session summaries

## Skill Examples

### Example 1: Trending Topic Scout - Multi-Session Comparison

**Session 1:**
```python
User: "Scout trending repos for 'kubernetes'"
Agent: [Executes skill]
Agent: "Kubernetes momentum: 138,632°F (spread: 64k, midpoint: 77k)"

# After 60 seconds, summary extracted:
# "User analysed trending kubernetes repositories. Found 50 repos with
#  momentum of 138,632°F. Top repo: kubernetes/kubernetes (109k stars)"
```

**Session 2 (weeks later):**
```python
User: "What was the kubernetes momentum last time I checked?"

# Agent queries summaries
past_summaries = summaries.retrieve_recent_summaries(
    actor_id="user123",
    query="kubernetes trending analysis"
)
# Retrieved: "Kubernetes momentum: 138,632°F"

Agent: "Last time you checked, kubernetes momentum was 138,632°F" ✅

User: "Scout it again now"
Agent: [Executes skill]
Agent: "Current kubernetes momentum: 145,890°F"
Agent: "That's up from 138,632°F last time! 📈" ✅
```

### Example 2: Repo Comparison - Decision Tracking

**Session 1:**
```python
User: "Compare anthropics/claude-sdk with openai/openai-sdk"
Agent: "Claude SDK: 4,200 stars, OpenAI SDK: 12,500 stars"
Agent: "OpenAI SDK has 3x more stars"

User: "We should contribute to Claude SDK to help it grow"
Agent: "Great idea! I'll note that decision"

# Summary extracted:
# "User compared Claude SDK (4.2k stars) vs OpenAI SDK (12.5k stars).
#  Decision: Contribute to Claude SDK to help ecosystem growth."
```

**Session 2 (next week):**
```python
User: "What did we decide about the Claude SDK?"

# Agent queries summaries
summaries_result = summaries.retrieve_recent_summaries(
    actor_id="user123",
    query="Claude SDK decision"
)
# Retrieved: "Decision: Contribute to Claude SDK to help ecosystem growth"

Agent: "You decided to contribute to Claude SDK to help it grow" ✅

User: "Has it grown since then?"
Agent: [Checks current stars]
Agent: "Claude SDK is now at 4,450 stars (up from 4,200) 📈"
```

### Example 3: Portfolio Summary - Progress Tracking

**Session 1 (January):**
```python
User: "Summarise my GitHub portfolio"
Agent: "Portfolio: 23 repos, 3,450 total stars, 150 avg stars, 302°F momentum"

# Summary extracted:
# "User's GitHub portfolio: 23 repositories, 3,450 total stars,
#  150 average stars per repo, momentum temperature 302°F"
```

**Session 2 (March):**
```python
User: "Summarise my portfolio again"
Agent: "Portfolio: 25 repos, 4,100 total stars, 164 avg stars, 338°F momentum"

User: "How does this compare to January?"

# Agent queries past summaries
past = summaries.retrieve_recent_summaries(
    actor_id="user123",
    query="portfolio summary January"
)
# Retrieved: "23 repos, 3,450 stars, 302°F"

Agent: "Great progress! ✅
  - Repos: 23 → 25 (+2)
  - Total stars: 3,450 → 4,100 (+650)
  - Avg stars: 150 → 164 (+14)
  - Momentum: 302°F → 338°F (+36°F) 🔥"
```

### Example 4: Complex Workflow - Session Recap

**Session 1 (Morning):**
```python
User: "Scout trending kubernetes repos"
Agent: [Executes skill]

User: "Compare the top 2"
Agent: [Compares kubernetes/kubernetes vs rancher/k3s]

User: "Search skills related to issue tracking"
Agent: [Finds issue_heat_map skill]

# Summary extracted:
# "User performed trending analysis on kubernetes (momentum: 138k°F),
#  compared top 2 repos (kubernetes/kubernetes: 109k vs rancher/k3s: 45k),
#  discovered issue_heat_map skill for future use"
```

**Session 2 (Afternoon):**
```python
User: "What was I working on this morning?"

# Agent retrieves session summary
morning_summary = summaries.retrieve_session_summary(
    actor_id="user123",
    session_id="session_morning_001"
)

Agent: "This morning you:
  1. Analysed trending kubernetes repos (momentum: 138k°F)
  2. Compared kubernetes/kubernetes (109k stars) vs rancher/k3s (45k stars)
  3. Found the issue_heat_map skill for tracking issue activity" ✅
```

### Example 5: Skill Testing - Test Session Summary

**Test Session:**
```python
# Testing trending_topic_scout with multiple topics
User: "Scout trending repos for 'docker'"
Agent: "Docker momentum: 95,421°F"

User: "Scout trending repos for 'python'"
Agent: "Python momentum: 112,305°F"

User: "Scout trending repos for 'rust'"
Agent: "Rust momentum: 89,245°F"

# Summary extracted:
# "User tested trending_topic_scout skill on three topics:
#  Docker (95k°F), Python (112k°F - highest), Rust (89k°F - lowest).
#  All executions successful."
```

**Evaluation Session:**
```python
User: "What were the results from yesterday's skill testing?"

# Retrieve test session summary
test_summary = summaries.retrieve_recent_summaries(
    actor_id="test_engineer",
    query="trending_topic_scout testing"
)

Agent: "Yesterday's testing results:
  - Docker: 95,421°F
  - Python: 112,305°F (highest)
  - Rust: 89,245°F (lowest)
  All executions completed successfully ✅"
```

## Evaluation Testing

### Test 1: Summary Generation

```python
def test_summary_generation():
    session_id = "test_session_summary_001"

    # Create multi-turn conversation
    memory.create_event("test_user", session_id, [
        ("Scout trending repos for 'kubernetes'", "USER"),
        ("Momentum: 138,632°F", "ASSISTANT"),
        ("Compare top 2", "USER"),
        ("kubernetes/kubernetes: 109k vs rancher/k3s: 45k", "ASSISTANT")
    ])

    # Wait for summary extraction
    time.sleep(70)

    # Retrieve summary
    summary = summaries.retrieve_session_summary(
        actor_id="test_user",
        session_id=session_id
    )

    # Validate summary exists and contains key points
    assert len(summary) > 0
    summary_text = summary[0].get('value', '')
    assert "kubernetes" in summary_text.lower()
    assert "momentum" in summary_text.lower() or "138" in summary_text
```

### Test 2: Cross-Session Retrieval

```python
def test_cross_session_retrieval():
    # Session 1
    memory.create_event("test_user", "session_001", [
        ("Analyse docker repos", "USER"),
        ("Docker: 95k°F", "ASSISTANT")
    ])

    # Session 2
    memory.create_event("test_user", "session_002", [
        ("Analyse python repos", "USER"),
        ("Python: 112k°F", "ASSISTANT")
    ])

    time.sleep(70)

    # Query across sessions
    summaries_result = summaries.retrieve_recent_summaries(
        actor_id="test_user",
        query="repository analysis"
    )

    # Validate both sessions retrieved
    assert len(summaries_result) >= 2
```

### Test 3: Summary Accuracy

```python
def test_summary_accuracy():
    session_id = "accuracy_test"

    # Conversation with specific facts
    memory.create_event("test_user", session_id, [
        ("Compare react and vue", "USER"),
        ("React: 210k stars, Vue: 205k stars", "ASSISTANT"),
        ("Calculate the difference", "USER"),
        ("5,000 stars difference", "ASSISTANT")
    ])

    time.sleep(70)

    summary = summaries.retrieve_session_summary("test_user", session_id)
    summary_text = summary[0].get('value', '')

    # Validate key facts in summary
    assert "react" in summary_text.lower()
    assert "vue" in summary_text.lower()
    assert "210" in summary_text or "5000" in summary_text or "5,000" in summary_text
```

## Best Practices

### 1. Query Summaries for "Last Time" Requests

```python
# Good: Detect temporal references
temporal_keywords = ["last time", "previously", "earlier", "before", "past session"]
if any(kw in user_message.lower() for kw in temporal_keywords):
    past_summaries = summaries.retrieve_recent_summaries(
        actor_id=actor_id,
        query=user_message,
        top_k=3
    )
    # Use summaries to answer
```

### 2. Provide Comparison Context

```python
# Good: Compare current vs past using summaries
current_result = execute_skill(user_message)

past_summary = summaries.retrieve_recent_summaries(
    actor_id=actor_id,
    query=f"previous {skill_name} execution"
)

if past_summary:
    return f"{current_result}\n\nCompared to last time: {past_summary[0].get('value')}"
```

### 3. Use Summaries for Onboarding

```python
# When new session starts
def get_onboarding_context(actor_id: str) -> str:
    """Provide context from recent sessions."""
    recent = summaries.retrieve_recent_summaries(
        actor_id=actor_id,
        query="recent activity",
        top_k=3
    )

    if not recent:
        return ""

    context = "## Recent Activity:\n"
    for summary in recent:
        context += f"- {summary.get('value', '')}\n"

    return context
```

### 4. Session ID Naming for Clarity

```python
# Good: Descriptive session IDs
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M')}_{task_type}"
# Example: session_20240115_1430_trending_analysis

# Bad: Opaque session IDs
session_id = str(uuid.uuid4())  # ❌ Hard to identify later
```

## Common Summary Patterns

### Conversation Summary
```
"User discussed kubernetes ecosystem. Compared kubernetes/kubernetes (109k stars)
with rancher/k3s (45k stars). Noted kubernetes dominance. No action items."
```

### Decision Summary
```
"User decided to focus contributions on Claude SDK to help ecosystem growth.
Noted current gap: Claude SDK 4.2k stars vs OpenAI SDK 12.5k stars."
```

### Analysis Summary
```
"User analysed trending repositories across 3 topics:
Docker (95k°F), Python (112k°F), Rust (89k°F). Python showed highest momentum."
```

### Workflow Summary
```
"Multi-step workflow completed: (1) Searched trending kubernetes repos,
(2) Calculated momentum: 138k°F, (3) Compared top 2 repos, (4) Saved results."
```

## Performance Metrics

Track these metrics for summary memory:
- **Summary extraction rate** - % of sessions that produce summaries
- **Summary completeness** - Key points captured vs missed
- **Retrieval accuracy** - Relevance of retrieved summaries to queries
- **Compression ratio** - Summary length vs full conversation length

## Limitations

- ❌ **60+ second delay** - Summaries not available immediately
- ❌ **Information loss** - Not all details captured in summary
- ❌ **Session-scoped** - One summary per session (can't summarise across sessions)
- ❌ **No control over content** - Can't specify what to include/exclude

## When to Use Other Strategies

- **Need immediate context** → Use [short_term.md](./short_term.md)
- **Learning from experiences** → Use [episodic.md](./episodic.md)
- **Learning user preferences** → Use [preference.md](./preference.md)
- **Building knowledge base** → Use [semantic.md](./semantic.md)

## Next Steps

1. Enable summary strategy in CDK MemoryConstruct
2. Implement SummaryMemory client in `src/agent/memory/summary.py`
3. Detect temporal references in user messages
4. Query past summaries for context
5. Test cross-session summary retrieval
6. Monitor summary completeness and accuracy
7. Build progress tracking features using summaries

Summary memory transforms scattered conversations into organised, retrievable session records.
