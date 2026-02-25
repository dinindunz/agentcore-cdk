# Short-Term Memory

## What It Is

Short-term memory stores **raw conversation events** within a single session. It captures the exact turn-by-turn interactions between user, assistant, and tools without any processing or extraction.

**Key Characteristics:**
- ✅ **Immediate availability** - no processing delay
- ✅ **Raw storage** - exact messages as sent
- ✅ **Session-scoped** - isolated per session
- ✅ **Chronological order** - maintains conversation flow

## When to Use

Use short-term memory for:
- ✅ **Multi-turn context** - "Convert that to Kelvin" (referring to previous result)
- ✅ **Pronoun resolution** - Understanding "it", "that", "the previous one"
- ✅ **Session continuity** - Maintaining context across multiple requests
- ✅ **Immediate retrieval** - Can't wait longer for extraction

## Agent Code Implementation

### Memory Client

```python
from datetime import datetime
from typing import List, Dict
import boto3


class ShortTermMemory:
    """Manages short-term conversation memory."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def create_event(
        self,
        actor_id: str,
        session_id: str,
        messages: List[tuple[str, str]],
    ) -> Dict:
        """Store conversation turn immediately."""
        payload = []
        for content, role in messages:
            payload.append({
                'conversational': {
                    'role': role,  # USER, ASSISTANT, TOOL
                    'content': {'text': content}
                }
            })

        return self.data_client.create_event(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            eventTimestamp=datetime.now(),
            payload=payload
        )

    def get_recent_context(
        self,
        actor_id: str,
        session_id: str,
        max_turns: int = 10,
    ) -> List[Dict]:
        """Retrieve recent conversation history for context."""
        response = self.data_client.list_events(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            maxResults=max_turns
        )
        # Reverse to get chronological order
        return list(reversed(response.get('events', [])))
```

### Integration with Agent

```python
# src/agent/main.py
from short_term_memory import ShortTermMemory

memory = ShortTermMemory(
    memory_id=os.environ["MEMORY_ID"],
    region_name=os.environ["REGION_NAME"]
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", "default_session")

    # 1. Retrieve recent context
    recent_context = memory.get_recent_context(
        actor_id=actor_id,
        session_id=session_id,
        max_turns=5
    )

    # 2. Build context string for agent
    context_messages = []
    for event in recent_context:
        for turn in event.get('payload', []):
            if 'conversational' in turn:
                role = turn['conversational']['role']
                text = turn['conversational']['content'].get('text', '')
                context_messages.append(f"{role}: {text}")

    context = "\n".join(context_messages) if context_messages else ""

    # 3. Enhance prompt with context
    enhanced_prompt = f"{context}\n\nUSER: {user_message}" if context else user_message

    # 4. Execute agent
    result = agent(enhanced_prompt)
    response_text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )

    # 5. Store interaction immediately
    memory.create_event(
        actor_id=actor_id,
        session_id=session_id,
        messages=[
            (user_message, "USER"),
            (response_text, "ASSISTANT")
        ]
    )

    return {"result": response_text}
```

## Namespace Pattern

Short-term memory doesn't use namespaces - it's organised by:
- **memoryId** - The memory resource
- **actorId** - User/customer identifier
- **sessionId** - Conversation session identifier

```
Memory ID: mem-abc123
├── Actor: user-sarah-123
│   ├── Session: session-2024-01-15-001
│   │   ├── Event 1: USER: "Convert 100F to Celsius"
│   │   ├── Event 2: ASSISTANT: "37.8°C"
│   │   └── Event 3: USER: "Now convert that to Kelvin"
│   └── Session: session-2024-01-16-001
│       └── Event 1: USER: "Scout trending repos"
```

## Skill Examples

### Example 1: Temperature Converter - Context Retention

**Without Short-Term Memory:**
```
User: "Convert 100F to Celsius"
Agent: "100°F is 37.8°C"

User: "Now convert that to Kelvin"
Agent: "I need to know what temperature to convert" ❌
```

**With Short-Term Memory:**
```python
# Turn 1
memory.create_event(
    actor_id="user123",
    session_id="session001",
    messages=[
        ("Convert 100F to Celsius", "USER"),
        ("temperature-converter___fahrenheit_to_celsius(100)", "TOOL"),
        ("{'result': 37.8}", "TOOL"),
        ("100°F is 37.8°C", "ASSISTANT")
    ]
)

# Turn 2
recent = memory.get_recent_context("user123", "session001", max_turns=2)
# Context shows: "100°F is 37.8°C"

User: "Now convert that to Kelvin"
Agent: [Uses context to understand "that" = 37.8°C]
Agent: "37.8°C is 310.95 Kelvin" ✅
```

### Example 2: Trending Topic Scout - Multi-Step Workflow

**Skill Steps:**
1. Search repositories
2. Calculate spread (subtract)
3. Calculate midpoint (add, divide)
4. Convert to temperature (celsius_to_fahrenheit)

**With Short-Term Memory:**
```python
# Store each tool invocation immediately
session_id = "session_trending_kubernetes"

# Step 1: Search
memory.create_event(
    actor_id="user123",
    session_id=session_id,
    messages=[
        ("Scout trending repos for 'kubernetes'", "USER"),
        ("github___searchRepositories(topic='kubernetes')", "TOOL"),
        ("Found: kubernetes/kubernetes (109k stars), rancher/k3s (45k stars)", "TOOL")
    ]
)

# Step 2: Calculate spread
memory.create_event(
    actor_id="user123",
    session_id=session_id,
    messages=[
        ("calculator___subtract(109000, 45000)", "TOOL"),
        ("{'result': 64000}", "TOOL"),
        ("Spread: 64,000 stars", "ASSISTANT")
    ]
)

# User can now ask follow-up questions with full context
User: "What was the spread again?"
# Retrieve recent context → Shows "Spread: 64,000 stars" ✅
```

### Example 3: Repo Comparison - Intermediate Values

**Without Short-Term Memory:**
```
User: "Compare facebook/react with vuejs/vue"
Agent: [Gets stars, calculates ratio, percentage]

User: "What were the exact star counts?"
Agent: "I don't have that information" ❌
```

**With Short-Term Memory:**
```python
memory.create_event(
    actor_id="user123",
    session_id="session_comparison",
    messages=[
        ("Compare facebook/react with vuejs/vue", "USER"),
        ("github___getRepository('facebook/react')", "TOOL"),
        ("{'stars': 210000}", "TOOL"),
        ("github___getRepository('vuejs/vue')", "TOOL"),
        ("{'stars': 205000}", "TOOL"),
        ("calculator___subtract(210000, 205000)", "TOOL"),
        ("{'result': 5000}", "TOOL"),
        ("React has 5,000 more stars", "ASSISTANT")
    ]
)

# Later in the session
User: "What were the exact star counts?"
recent = memory.get_recent_context("user123", "session_comparison", max_turns=5)
# Context shows tool results: 210,000 and 205,000
Agent: "React had 210,000 stars and Vue had 205,000 stars" ✅
```

### Example 4: Skill Search - Progressive Refinement

```python
# Turn 1: Initial search
memory.create_event(
    actor_id="user123",
    session_id="session_skill_search",
    messages=[
        ("Find me a skill for GitHub analysis", "USER"),
        ("skill-search___search_skills(query='GitHub analysis')", "TOOL"),
        ("Found: trending_topic_scout, repo_comparison, portfolio_summary", "TOOL"),
        ("I found 3 skills for GitHub analysis", "ASSISTANT")
    ]
)

# Turn 2: Refinement with context
User: "Which one calculates temperature?"
# Retrieve context → Shows the 3 skill names
Agent: "trending_topic_scout uses temperature conversion" ✅
```

## Evaluation Testing

### Test 1: Context Retention Accuracy

```python
def test_context_retention():
    session_id = "test_session_001"

    # Turn 1
    memory.create_event("test_user", session_id, [
        ("Convert 100F to Celsius", "USER"),
        ("37.8°C", "ASSISTANT")
    ])

    # Turn 2
    context = memory.get_recent_context("test_user", session_id, max_turns=2)

    # Validate context contains Turn 1
    assert any("100F" in str(event) for event in context)
    assert any("37.8°C" in str(event) for event in context)
```

### Test 2: Pronoun Resolution

```python
def test_pronoun_resolution():
    # Test if agent can resolve "that" using short-term memory

    # Turn 1
    response1 = invoke_agent("Calculate 50 + 30", session_id="test_002")
    # Expected: "80"

    # Turn 2
    response2 = invoke_agent("Multiply that by 2", session_id="test_002")
    # Expected: Agent understands "that" = 80, returns "160"

    assert "160" in response2
```

### Test 3: Tool Call Tracking

```python
def test_tool_call_history():
    session_id = "test_session_003"

    # Execute skill with multiple tool calls
    invoke_agent("Scout trending repos for 'python'", session_id=session_id)

    # Retrieve context
    context = memory.get_recent_context("test_user", session_id, max_turns=10)

    # Extract tool calls
    tool_calls = [
        event for event in context
        if any(turn.get('conversational', {}).get('role') == 'TOOL' for turn in event.get('payload', []))
    ]

    # Validate tool sequence
    expected_tools = ["searchRepositories", "subtract", "add", "divide", "celsius_to_fahrenheit"]
    # Check tool calls match expected sequence
```

## Best Practices

### 1. Buffer Conversation Turns

```python
class ConversationBuffer:
    """Buffer turns before flushing to memory."""

    def __init__(self, memory: ShortTermMemory, actor_id: str, session_id: str):
        self.memory = memory
        self.actor_id = actor_id
        self.session_id = session_id
        self._buffer: List[tuple[str, str]] = []

    def add(self, content: str, role: str):
        self._buffer.append((content, role))

    def flush(self):
        if self._buffer:
            self.memory.create_event(
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=self._buffer
            )
            self._buffer = []
```

### 2. Include Tool Calls in Events

```python
# Good: Store tool invocations
memory.create_event(
    actor_id="user123",
    session_id="session001",
    messages=[
        ("Convert 100F to C", "USER"),
        ("temperature-converter___fahrenheit_to_celsius(100)", "TOOL"),  # ✅
        ("{'result': 37.8}", "TOOL"),  # ✅
        ("37.8°C", "ASSISTANT")
    ]
)

# Bad: Only store user and assistant messages
memory.create_event(
    actor_id="user123",
    session_id="session001",
    messages=[
        ("Convert 100F to C", "USER"),
        ("37.8°C", "ASSISTANT")
    ]
)  # ❌ Missing tool context
```

### 3. Limit Context Window

```python
# Good: Retrieve last 5-10 turns for performance
context = memory.get_recent_context("user123", "session001", max_turns=5)

# Bad: Retrieve entire session history (can be hundreds of turns)
context = memory.get_recent_context("user123", "session001", max_turns=1000)  # ❌ Slow
```

### 4. Session ID Strategy

```python
import uuid
from datetime import datetime

# Good: Unique session per conversation
session_id = f"session_{uuid.uuid4()}"

# Or: Date-based sessions
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Bad: Reusing session IDs across different conversations
session_id = "default_session"  # ❌ Mixes unrelated conversations
```

## Limitations

- ❌ **No semantic search** - Can't query "show me all temperature conversions"
- ❌ **Session-scoped only** - Can't retrieve context from previous sessions
- ❌ **No extraction** - Doesn't learn preferences or patterns
- ❌ **Storage costs** - Raw events consume more storage than extracted insights
- ❌ **Expiration** - Events expire after configured duration (e.g., 90 days)

## When to Upgrade to Long-Term Memory

Consider adding long-term strategies when:
- ✅ Need to recall information from previous sessions
- ✅ Want to learn user preferences automatically
- ✅ Need semantic search ("show me all kubernetes analyses")
- ✅ Building knowledge bases from conversations
- ✅ Tracking patterns across multiple sessions

See: [episodic.md](./episodic.md), [preference.md](./preference.md), [summary.md](./summary.md), [semantic.md](./semantic.md)

## Performance Metrics

Track these metrics for short-term memory:
- **Context retrieval latency** - Time to fetch recent events
- **Context relevance** - Does retrieved context help resolve pronouns?
- **Session continuity** - % of multi-turn conversations that maintain coherence
- **Storage efficiency** - Events stored vs. events retrieved

## Next Steps

1. Implement ShortTermMemory client in `src/agent/memory/short_term.py`
2. Integrate with agent runtime in `src/agent/main.py`
3. Add context retrieval before each agent invocation
4. Test with multi-turn conversation prompts
5. Monitor context relevance and retrieval latency

Once short-term memory is working, add long-term strategies for cross-session intelligence.
