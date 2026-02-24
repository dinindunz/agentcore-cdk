# Episodic Memory

## What It Is

Episodic memory captures **specific events and experiences** as structured records with situation, intent, assessment, justification, and learnings. It's designed to help agents recall "what happened when..." and learn from past successes and failures.

**Key Characteristics:**
- ✅ **Structured episodes** - Not raw text, but organised insights
- ✅ **Cross-session** - Recall experiences from any past session
- ✅ **Reflection support** - Generates insights across multiple episodes
- ✅ **Intent-indexed** - Search by what user was trying to achieve
- ✅ **60+ second extraction** - Asynchronous processing from short-term events

## Episode Structure

Each episode contains:
- **Situation** - What was the context?
- **Intent** - What was the user trying to achieve?
- **Assessment** - Did the action succeed or fail?
- **Justification** - Why did the agent choose this approach?
- **Reflection** - What lessons were learned?

Example:
```xml
<episode>
  <situation>User requested trending repository analysis for 'kubernetes'</situation>
  <intent>Find popular kubernetes projects and calculate momentum metric</intent>
  <assessment>Successfully retrieved 50 repos, calculated spread of 64k stars, converted to 138,632°F</assessment>
  <justification>Used trending_topic_scout skill with GitHub API + calculator + temperature converter</justification>
  <reflection>Temperature metaphor resonated well with user. Calculator arithmetic was accurate.</reflection>
</episode>
```

## When to Use

Use episodic memory for:
- ✅ **Learning from experience** - "Last time I did X, what happened?"
- ✅ **Workflow resumption** - Resume interrupted multi-step tasks
- ✅ **Pattern recognition** - "This is similar to when user asked about Y"
- ✅ **Success tracking** - "Which approaches worked well?"
- ✅ **Failure analysis** - "Why did this fail last time?"

## Agent Code Implementation

### Memory Client

```python
from typing import List, Dict, Optional
import boto3


class EpisodicMemory:
    """Manages episodic memory for learning from past experiences."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def retrieve_similar_episodes(
        self,
        actor_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve episodes similar to current task.

        Args:
            actor_id: User identifier
            query: Semantic query describing current task
            session_id: Optional - limit to specific session
            top_k: Number of episodes to return

        Returns:
            List of episode records with situation/intent/assessment
        """
        if session_id:
            namespace = f"/strategies/episodic/actors/{actor_id}/sessions/{session_id}/"
        else:
            namespace = f"/strategies/episodic/actors/{actor_id}/"

        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=namespace,
            searchCriteria={"searchQuery": query},
            maxResults=top_k
        )
        return response.get('memoryRecordSummaries', [])

    def retrieve_reflections(
        self,
        actor_id: str,
        query: str,
        top_k: int = 3,
    ) -> List[Dict]:
        """
        Retrieve high-level reflections across multiple episodes.

        Reflections are insights like:
        - "User prefers detailed error explanations"
        - "Calculator tools work well for kubernetes repos"
        - "GitHub API rate limits occur after 20 consecutive requests"
        """
        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/episodic/actors/{actor_id}/",  # Actor-level reflections
            searchCriteria={"searchQuery": query},
            maxResults=top_k
        )
        # Filter for reflection records
        return [
            record for record in response.get('memoryRecordSummaries', [])
            if 'reflection' in record.get('key', '').lower()
        ]
```

### Integration with Agent

```python
# src/agent/main.py
from episodic_memory import EpisodicMemory

episodic = EpisodicMemory(
    memory_id=os.environ["MEMORY_ID"],
    region_name=os.environ["REGION_NAME"]
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", f"session_{uuid.uuid4()}")

    # 1. Query for similar past episodes
    episodes = episodic.retrieve_similar_episodes(
        actor_id=actor_id,
        query=f"Similar task: {user_message}",
        top_k=3
    )

    # 2. Build episode context
    episode_context = ""
    if episodes:
        episode_context = "\n\n## Relevant Past Episodes:\n"
        for ep in episodes:
            episode_context += f"**Episode**: {ep.get('value', '')}\n\n"

    # 3. Query for reflections (learnings across episodes)
    reflections = episodic.retrieve_reflections(
        actor_id=actor_id,
        query=f"Lessons learned about: {user_message}",
        top_k=2
    )

    reflection_context = ""
    if reflections:
        reflection_context = "\n## Lessons Learned:\n"
        for ref in reflections:
            reflection_context += f"- {ref.get('value', '')}\n"

    # 4. Enhance prompt with episodic context
    enhanced_prompt = f"{episode_context}{reflection_context}\n## Current Request:\n{user_message}"

    # 5. Execute agent with episodic insights
    result = agent(enhanced_prompt)
    response_text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )

    return {"result": response_text}

    # Note: Episode extraction happens automatically after CreateEvent (60+ sec delay)
```

## Namespace Patterns

### Session-Level Episodes
```
/strategies/episodic/actors/{actorId}/sessions/{sessionId}/
```
**Use for**: Episodes specific to a single session
```
/strategies/episodic/actors/user-sarah-123/sessions/session-2024-01-15-001/episode-kubernetes-trending
/strategies/episodic/actors/user-sarah-123/sessions/session-2024-01-15-001/episode-react-vue-comparison
```

### Actor-Level Reflections
```
/strategies/episodic/actors/{actorId}/
```
**Use for**: Cross-session insights and patterns
```
/strategies/episodic/actors/user-sarah-123/reflection-temperature-metaphor-preference
/strategies/episodic/actors/user-sarah-123/reflection-calculator-accuracy-pattern
```

## Skill Examples

### Example 1: Trending Topic Scout - Learning from Past Analysis

**First Execution (Session 1):**
```python
User: "Scout trending repos for 'kubernetes'"

# Agent executes skill, stores event
# After 60+ seconds, episodic memory extracts:

Episode:
- Situation: User researching kubernetes ecosystem popularity
- Intent: Find top repositories and calculate momentum metric
- Assessment: Success - retrieved 50 repos, spread 64k, momentum 138,632°F
- Justification: Used trending_topic_scout skill → searchRepositories → calculator → temperature_converter
- Reflection: User engaged with temperature metaphor. All calculations were accurate.
```

**Second Execution (Session 2, weeks later):**
```python
User: "Scout trending repos for 'docker'"

# Before execution, agent queries episodic memory
episodes = episodic.retrieve_similar_episodes(
    actor_id="user123",
    query="trending repository analysis with momentum calculation"
)

# Retrieved episode shows:
# "Last time user analysed 'kubernetes', they liked the temperature metaphor"

# Agent applies learned approach
Agent: "Docker momentum: 95,421°F 🔥" ✅
```

### Example 2: Interrupted Workflow Recovery

**Session 1 - Interrupted:**
```python
User: "Create a heat map of kubernetes issues"

# Agent starts execution
# Step 1: searchRepositories('kubernetes') → 50 repos ✅
# Step 2: Process first 10 repos → extract issue counts ✅
# Step 3: ... [CONNECTION TIMEOUT]

# Episodic memory extracts (after 60s):
Episode:
- Situation: User requested issue heat map for kubernetes
- Intent: Analyse issue activity across kubernetes repos
- Assessment: INCOMPLETE - processed 10/50 repos before interruption
- Justification: Started with searchRepositories, then iterating through results
- Reflection: Need to handle partial completion better
```

**Session 2 - Resumption:**
```python
User: "Continue my kubernetes heat map"

# Agent queries episodic memory
episodes = episodic.retrieve_similar_episodes(
    actor_id="user123",
    query="incomplete kubernetes issue heat map",
    top_k=1
)

# Retrieved episode shows:
# "Processed 10/50 repos, extracted issue counts: [234, 156, 89, ...]"

# Agent resumes from repo 11
Agent: "Resuming kubernetes heat map from repo 11/50..." ✅
Agent: [Completes remaining 40 repos]
Agent: "Heat map complete! Top 5 hottest repos: ..." ✅
```

### Example 3: Skill Failure Pattern Recognition

**Multiple Sessions with Failures:**
```python
# Session 1
User: "Scout trending repos for 'obscure-topic'"
# Only 3 repos found → Temperature calculation seems meaningless
Episode Assessment: "Partial success - insufficient data for meaningful momentum"

# Session 2
User: "Scout trending repos for 'niche-framework'"
# 5 repos found → Same issue
Episode Assessment: "Partial success - insufficient repos for trend analysis"

# After multiple episodes, reflection generated:
Reflection:
"Trending topic scout skill requires 20+ repos for meaningful analysis.
When fewer than 10 repos exist, suggest alternative like 'repo comparison' instead."
```

**Future Session:**
```python
User: "Scout trending repos for 'new-tech'"

# Agent queries reflections
reflections = episodic.retrieve_reflections(
    actor_id="user123",
    query="trending topic scout limitations"
)

# Retrieved reflection: "Need 20+ repos for meaningful analysis"

Agent: [Searches first]
Agent: "I found only 8 repos for 'new-tech'. Would you like me to compare
        the top 2 instead using the repo comparison skill?" ✅
```

### Example 4: Tool Combination Patterns

**Learning Successful Patterns:**
```python
# Episodes show successful tool combinations:

Episode 1: searchRepositories → subtract → add → divide → celsius_to_fahrenheit
Assessment: Success ✅

Episode 2: searchRepositories → subtract → multiply
Assessment: Success ✅

Episode 3: searchRepositories → divide (tried to divide repos directly)
Assessment: Failed - division without context didn't make sense ❌

# Reflection generated:
"When analysing GitHub trends:
 - Calculator tools (subtract, add, divide) work well AFTER extracting star counts
 - Temperature conversion adds engaging presentation
 - Direct mathematical operations on repository objects fail"
```

**Applying Learned Pattern:**
```python
User: "Analyse trending python repos"

# Agent queries reflections
reflections = episodic.retrieve_reflections(
    actor_id="user123",
    query="successful GitHub analysis tool patterns"
)

# Retrieved: "Extract star counts first, then use calculator"

# Agent follows learned pattern
Agent: ✅ searchRepositories → extract stars → calculator → temperature_converter
```

## Evaluation Testing

### Test 1: Episode Retrieval Accuracy

```python
def test_episode_retrieval():
    # Create episode via event
    memory.create_event(
        actor_id="test_user",
        session_id="test_session_001",
        messages=[
            ("Scout trending repos for 'kubernetes'", "USER"),
            ("searchRepositories(topic='kubernetes')", "TOOL"),
            ("Found 50 repos, top: 109k stars", "TOOL"),
            ("Kubernetes momentum: 138,632°F", "ASSISTANT")
        ]
    )

    # Wait for extraction
    time.sleep(70)

    # Query for similar episodes
    episodes = episodic.retrieve_similar_episodes(
        actor_id="test_user",
        query="trending repository analysis"
    )

    # Validate episode was extracted
    assert len(episodes) > 0
    assert "kubernetes" in str(episodes[0]).lower()
    assert "momentum" in str(episodes[0]).lower()
```

### Test 2: Workflow Resumption

```python
def test_workflow_resumption():
    # Session 1: Start workflow
    memory.create_event("test_user", "session_001", [
        ("Start heat map for kubernetes", "USER"),
        ("Processing repo 1/50: kubernetes/kubernetes", "TOOL"),
        ("Processing repo 10/50: rancher/k3s", "TOOL"),
        # Interrupted
    ])

    time.sleep(70)

    # Session 2: Resume
    episodes = episodic.retrieve_similar_episodes(
        actor_id="test_user",
        query="incomplete heat map workflow"
    )

    # Validate episode shows partial completion
    episode_text = episodes[0].get('value', '')
    assert "10/50" in episode_text or "incomplete" in episode_text.lower()
```

### Test 3: Pattern Recognition Across Episodes

```python
def test_pattern_recognition():
    # Create multiple similar episodes
    for topic in ["kubernetes", "docker", "python"]:
        memory.create_event("test_user", f"session_{topic}", [
            (f"Scout trending repos for '{topic}'", "USER"),
            (f"Momentum: XXX°F", "ASSISTANT")
        ])

    time.sleep(70)

    # Query for reflections
    reflections = episodic.retrieve_reflections(
        actor_id="test_user",
        query="trending repository analysis patterns"
    )

    # Validate reflection was generated across episodes
    assert len(reflections) > 0
```

## Best Practices

### 1. Include Tool Results in Events

```python
# Good: Include tool results for better episode extraction
memory.create_event(
    actor_id="user123",
    session_id="session001",
    messages=[
        ("Scout trending repos for 'rust'", "USER"),
        ("searchRepositories(topic='rust')", "TOOL"),
        ("{'repos': 45, 'top_stars': 89000, 'bottom_stars': 12000}", "TOOL"),  # ✅
        ("calculator___subtract(89000, 12000)", "TOOL"),
        ("{'result': 77000}", "TOOL"),  # ✅
        ("Rust momentum: 138,632°F", "ASSISTANT")
    ]
)
```

### 2. Query Before Execution

```python
# Always check for relevant episodes before starting new task
episodes = episodic.retrieve_similar_episodes(
    actor_id=actor_id,
    query=f"Past experience with: {user_message}",
    top_k=3
)

if episodes:
    # Use episode insights to inform approach
    past_approach = extract_approach(episodes[0])
    apply_learned_approach(past_approach)
```

### 3. Use Reflections for Meta-Learning

```python
# Query reflections to learn from patterns
reflections = episodic.retrieve_reflections(
    actor_id=actor_id,
    query="common failure patterns"
)

# Apply meta-learnings to avoid past mistakes
for reflection in reflections:
    if "rate limit" in reflection.get('value', '').lower():
        # Add delay between requests
        enable_rate_limit_protection()
```

### 4. Scope Episodes Appropriately

```python
# Session-scoped: Use for task-specific episodes
episodic.retrieve_similar_episodes(
    actor_id="user123",
    query="kubernetes analysis",
    session_id="session_001"  # Only this session
)

# Actor-scoped: Use for learning across all sessions
episodic.retrieve_similar_episodes(
    actor_id="user123",
    query="kubernetes analysis",
    session_id=None  # All sessions
)
```

## Privacy Considerations

⚠️ **Important**: Reflections can span multiple actors by default.

If cross-actor reflections raise privacy concerns:
- Use **actor-level namespaces** for reflections: `/strategies/episodic/actors/{actorId}/`
- Apply **guardrails** to filter sensitive information
- Configure **session-scoped episodes** only: `/strategies/episodic/actors/{actorId}/sessions/{sessionId}/`

## Performance Metrics

Track these metrics for episodic memory:
- **Episode extraction success rate** - % of events that produce episodes
- **Episode retrieval relevance** - Similarity between query and retrieved episodes
- **Workflow resumption success** - % of interrupted tasks successfully resumed
- **Pattern application rate** - How often past learnings are applied

## Limitations

- ❌ **60+ second delay** - Episodes aren't available immediately
- ❌ **Extraction required** - Need significant tool activity for meaningful episodes
- ❌ **Query-dependent** - Retrieval quality depends on query phrasing
- ❌ **Not guaranteed** - Episode generation depends on AI assessment of "completeness"

## When to Use Other Strategies

- **Need immediate context** → Use [short_term.md](./short_term.md)
- **Learning user preferences** → Use [preference.md](./preference.md)
- **Building knowledge base** → Use [semantic.md](./semantic.md)
- **Session summaries** → Use [summary.md](./summary.md)

## Next Steps

1. Enable episodic strategy in CDK MemoryConstruct
2. Implement EpisodicMemory client in `src/agent/memory/episodic.py`
3. Query episodes before skill execution in agent
4. Test workflow interruption and resumption
5. Monitor episode extraction success rate
6. Build reflection-based meta-learning system

Episodic memory shines when your agent needs to learn from experience and handle complex, multi-step workflows.
