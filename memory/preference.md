# Preference Memory

## What It Is

Preference memory automatically **learns and stores user preferences, habits, and behavioral patterns** from conversations. It enables personalised agent behavior without users repeating their preferences every session.

**Key Characteristics:**
- ✅ **Automatic extraction** - No explicit "remember my preference" needed
- ✅ **Cross-session** - Preferences persist across all sessions
- ✅ **User-scoped** - Organised by actor (not session)
- ✅ **Proactive application** - Agent applies preferences without being asked
- ✅ **60+ second extraction** - Asynchronous processing from short-term events

## When to Use

Use preference memory for:
- ✅ **Personalisation** - "User prefers Celsius over Fahrenheit"
- ✅ **Habit learning** - "User always checks kubernetes repos on Mondays"
- ✅ **Style preferences** - "User likes concise responses with emojis"
- ✅ **Workflow preferences** - "User prefers skill search before direct tool use"
- ✅ **Reducing repetition** - Apply learned preferences automatically

## Agent Code Implementation

### Memory Client

```python
from typing import List, Dict
import boto3


class PreferenceMemory:
    """Manages user preference learning and application."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def retrieve_preferences(
        self,
        actor_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve user preferences using semantic query.

        Args:
            actor_id: User identifier
            query: Natural language query about preferences
            top_k: Number of preference records to return

        Returns:
            List of preference records
        """
        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/preferences/actors/{actor_id}/",
            searchCriteria={"searchQuery": query},
            maxResults=top_k
        )
        return response.get('memoryRecordSummaries', [])

    def get_all_preferences(
        self,
        actor_id: str,
        max_results: int = 20,
    ) -> List[Dict]:
        """
        List all known preferences for a user.

        Useful for building user profiles or debugging.
        """
        response = self.data_client.list_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/preferences/actors/{actor_id}/",
            maxResults=max_results
        )
        return response.get('memoryRecordSummaries', [])
```

### Integration with Agent

```python
# src/agent/main.py
from preference_memory import PreferenceMemory

preferences = PreferenceMemory(
    memory_id=os.environ["MEMORY_ID"],
    region_name=os.environ["REGION_NAME"]
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", f"session_{uuid.uuid4()}")

    # 1. Query user preferences
    user_prefs = preferences.retrieve_preferences(
        actor_id=actor_id,
        query="user preferences for responses and tools",
        top_k=10
    )

    # 2. Build preference context for system prompt
    pref_context = ""
    if user_prefs:
        pref_context = "\n\n## User Preferences:\n"
        for pref in user_prefs:
            pref_context += f"- {pref.get('value', '')}\n"

    # 3. Enhance system prompt with preferences
    enhanced_system_prompt = agent.system_prompt + pref_context

    # 4. Check for task-specific preferences
    if "temperature" in user_message.lower() or "convert" in user_message.lower():
        temp_prefs = preferences.retrieve_preferences(
            actor_id=actor_id,
            query="temperature unit preference",
            top_k=1
        )
        if temp_prefs:
            preferred_unit = extract_unit(temp_prefs[0].get('value', ''))
            # Proactively use preferred unit

    # 5. Execute agent with preference-aware prompt
    result = agent(user_message, system_prompt=enhanced_system_prompt)
    response_text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )

    return {"result": response_text}

    # Note: Preferences extracted automatically from CreateEvent (60+ sec delay)
```

## Namespace Pattern

### User-Level Preferences
```
/strategies/preferences/actors/{actorId}/
```
**Always user-scoped** - No session ID (preferences persist across sessions)

```
/strategies/preferences/actors/user-sarah-123/temperature-unit-celsius
/strategies/preferences/actors/user-sarah-123/response-style-concise
/strategies/preferences/actors/user-sarah-123/emoji-usage-yes
/strategies/preferences/actors/user-sarah-123/default-github-org-kubernetes
```

## Skill Examples

### Example 1: Temperature Unit Preference

**Session 1 - Learning Phase:**
```python
User: "Convert 100F to Celsius"
Agent: "100°F is 37.8°C"

User: "What's 75F in Celsius?"
Agent: "75°F is 23.9°C"

User: "I prefer Celsius, always show me Celsius"
Agent: "Got it! I'll use Celsius by default"

# After 60+ seconds, preference memory extracts:
# Preference: "User prefers Celsius over Fahrenheit for temperature"
```

**Session 2 - Application Phase (weeks later):**
```python
User: "What's the temperature for boiling water?"

# Agent queries preferences
prefs = preferences.retrieve_preferences(
    actor_id="user123",
    query="temperature unit preference"
)
# Retrieved: "User prefers Celsius"

Agent: "Boiling water is 100°C" ✅  # Automatically uses Celsius without being asked
```

### Example 2: Portfolio Summary - Presentation Style

**Session 1 - Learning:**
```python
User: "Summarise my GitHub portfolio"
Agent: """
Portfolio Summary:
- Total repositories: 23
- Total stars: 3,450
- Average stars per repo: 150
- Portfolio momentum: 302°F
"""

User: "I love the temperature metaphor! Always use that"
Agent: "Will do! I'll include momentum temperature in portfolio summaries"

# Preference extracted:
# "User likes temperature metaphors for GitHub metrics"
```

**Session 2 - Automatic Application:**
```python
User: "Show my portfolio stats"

# Agent queries preferences
prefs = preferences.retrieve_preferences(
    actor_id="user123",
    query="portfolio presentation preferences"
)
# Retrieved: "User likes temperature metaphors"

# Agent automatically includes temperature without being asked
Agent: """
Portfolio: 24 repos, 3,680 stars
Temperature: 315°F 🔥  ✅  # Proactively included based on preference
"""
```

### Example 3: Trending Topic Scout - Output Format

**Session 1 - Implicit Learning:**
```python
User: "Scout trending repos for 'kubernetes'"
Agent: "Kubernetes momentum: 138,632°F (spread: 64,000 stars, midpoint: 77,000)"

User: "That's too detailed. Just give me the temperature"
Agent: "Got it. Kubernetes: 138,632°F"

# Preference extracted:
# "User prefers concise output, temperature only (no intermediate calculations)"
```

**Session 2 - Same User:**
```python
User: "Scout trending repos for 'docker'"

# Agent queries preferences
prefs = preferences.retrieve_preferences(
    actor_id="user123",
    query="trending scout output format"
)
# Retrieved: "Concise output, temperature only"

Agent: "Docker: 95,421°F 🔥" ✅  # No spread/midpoint details
```

**Session 3 - Different User (no preferences):**
```python
User: "Scout trending repos for 'rust'"

# No preferences found for this user
# Agent uses default verbose output

Agent: "Rust momentum: 89,245°F (spread: 48,000 stars, midpoint: 50,500)" ✅
```

### Example 4: Skill Search - Tool Selection Preference

**Session 1 - Learning Tool Preference:**
```python
User: "Find me GitHub analysis skills"
Agent: [Lists: trending_topic_scout, repo_comparison, portfolio_summary]

User: "Use trending topic scout for kubernetes"
Agent: [Executes skill]

User: "Use trending topic scout for docker"
Agent: [Executes skill]

User: "Use trending topic scout for python"
Agent: [Executes skill]

# Preference extracted after multiple uses:
# "User's preferred skill for trending analysis: trending_topic_scout"
```

**Session 2 - Proactive Suggestion:**
```python
User: "Analyse trending rust repos"

# Agent queries preferences
prefs = preferences.retrieve_preferences(
    actor_id="user123",
    query="preferred skill for trending analysis"
)
# Retrieved: "User prefers trending_topic_scout"

Agent: "I'll use the trending topic scout skill (your usual choice for this type of analysis)" ✅
Agent: [Executes trending_topic_scout]
```

### Example 5: Response Style - Emoji Usage

**Session 1 - Implicit Preference:**
```python
User: "Compare react and vue repos"
Agent: "React has 210k stars, Vue has 205k stars. React is ahead by 5k"

User: "Make it more fun!"
Agent: "React: 210k ⭐ vs Vue: 205k ⭐ → React wins by 5k! 🎉"

User: "Much better!"

# Preference extracted:
# "User prefers responses with emojis and enthusiastic tone"
```

**Session 2 - Automatic Style Application:**
```python
User: "Compare kubernetes and docker repos"

# Agent queries preferences
prefs = preferences.retrieve_preferences(
    actor_id="user123",
    query="response style preferences"
)
# Retrieved: "User prefers emojis and enthusiastic tone"

Agent: "Kubernetes: 109k ⭐ vs Docker: 78k ⭐ → Kubernetes leads by 31k! 🚀" ✅
```

## Evaluation Testing

### Test 1: Preference Extraction

```python
def test_preference_extraction():
    # Session 1: Express preference
    memory.create_event("test_user", "session_001", [
        ("Convert to Celsius please", "USER"),
        ("37.8°C", "ASSISTANT"),
        ("Always use Celsius", "USER"),
        ("Got it!", "ASSISTANT")
    ])

    # Wait for extraction
    time.sleep(70)

    # Query preferences
    prefs = preferences.retrieve_preferences(
        actor_id="test_user",
        query="temperature unit"
    )

    # Validate extraction
    assert len(prefs) > 0
    assert "celsius" in str(prefs[0]).lower()
```

### Test 2: Cross-Session Preference Application

```python
def test_cross_session_application():
    # Session 1: Learn preference
    invoke_agent("I prefer concise responses", session_id="session_001", actor_id="test_user")
    time.sleep(70)

    # Session 2: New session, should apply preference
    response = invoke_agent("Scout trending repos", session_id="session_002", actor_id="test_user")

    # Validate concise format used
    assert len(response) < 100  # Concise response
    assert "spread" not in response.lower()  # No detailed breakdown
```

### Test 3: User-Specific Preferences

```python
def test_user_specific_preferences():
    # User A: Prefers Celsius
    invoke_agent("Use Celsius", session_id="s1", actor_id="user_a")
    time.sleep(70)

    # User B: Prefers Fahrenheit
    invoke_agent("Use Fahrenheit", session_id="s2", actor_id="user_b")
    time.sleep(70)

    # Test User A
    response_a = invoke_agent("What's boiling point?", actor_id="user_a")
    assert "100°C" in response_a or "celsius" in response_a.lower()

    # Test User B
    response_b = invoke_agent("What's boiling point?", actor_id="user_b")
    assert "212°F" in response_b or "fahrenheit" in response_b.lower()
```

## Best Practices

### 1. Query Preferences Before Task Execution

```python
# Good: Check preferences before starting
if "temperature" in user_message:
    temp_prefs = preferences.retrieve_preferences(
        actor_id=actor_id,
        query="temperature unit preference"
    )
    if temp_prefs:
        use_preferred_unit(temp_prefs[0])

# Bad: Assume defaults without checking
default_unit = "Fahrenheit"  # ❌ Ignores user preference
```

### 2. Build Preference Profiles

```python
def build_user_profile(actor_id: str) -> dict:
    """Build comprehensive user profile from preferences."""
    all_prefs = preferences.get_all_preferences(actor_id)

    profile = {
        "temperature_unit": None,
        "response_style": None,
        "emoji_usage": None,
        "preferred_skills": [],
    }

    for pref in all_prefs:
        value = pref.get('value', '').lower()
        if "celsius" in value:
            profile["temperature_unit"] = "celsius"
        elif "fahrenheit" in value:
            profile["temperature_unit"] = "fahrenheit"
        if "concise" in value:
            profile["response_style"] = "concise"
        if "emoji" in value:
            profile["emoji_usage"] = True

    return profile
```

### 3. Handle Missing Preferences Gracefully

```python
# Good: Fallback to defaults when no preference exists
prefs = preferences.retrieve_preferences(actor_id, "temperature unit")
unit = extract_unit(prefs[0]) if prefs else "celsius"  # Default

# Bad: Crash when preferences don't exist
prefs = preferences.retrieve_preferences(actor_id, "temperature unit")
unit = extract_unit(prefs[0])  # ❌ Crashes if prefs is empty
```

### 4. Update System Prompt Dynamically

```python
def build_preference_aware_prompt(actor_id: str, base_prompt: str) -> str:
    """Enhance system prompt with user preferences."""
    prefs = preferences.get_all_preferences(actor_id, max_results=10)

    if not prefs:
        return base_prompt

    pref_instructions = "\n\n## User Preferences:\n"
    for pref in prefs:
        pref_instructions += f"- {pref.get('value', '')}\n"

    return base_prompt + pref_instructions
```

## Common Preference Types

### Format Preferences
- Concise vs detailed responses
- With/without emojis
- Technical vs conversational language
- Bullet points vs paragraphs

### Unit Preferences
- Temperature: Celsius vs Fahrenheit
- Distance: Miles vs kilometers
- Date format: MM/DD/YYYY vs DD/MM/YYYY

### Tool/Skill Preferences
- Preferred skill for specific tasks
- Tool usage patterns (calculator vs estimation)
- GitHub org focus (kubernetes vs docker)

### Workflow Preferences
- Skill-first vs tool-first approach
- Confirmation before execution
- Progress updates during long tasks

## Performance Metrics

Track these metrics for preference memory:
- **Preference extraction rate** - % of conversations that yield preferences
- **Preference application rate** - How often preferences are used
- **User satisfaction** - Feedback on personalised responses
- **Preference accuracy** - Correct interpretation of user preferences

## Limitations

- ❌ **60+ second delay** - New preferences not available immediately
- ❌ **Implicit extraction** - May misinterpret casual comments as preferences
- ❌ **No explicit management** - Users can't view/edit preferences directly
- ❌ **Overwrite behavior** - Newer preferences may override older ones

## When to Use Other Strategies

- **Need immediate context** → Use [short_term.md](./short_term.md)
- **Learning from experiences** → Use [episodic.md](./episodic.md)
- **Building knowledge base** → Use [semantic.md](./semantic.md)
- **Session summaries** → Use [summary.md](./summary.md)

## Privacy Considerations

⚠️ **Preference data persistence:**
- Preferences persist across sessions indefinitely (until event expiry)
- Consider data retention policies for compliance
- Allow users to request preference deletion if needed

## Next Steps

1. Enable preference strategy in CDK MemoryConstruct
2. Implement PreferenceMemory client in `src/agent/memory/preference.py`
3. Query preferences before skill execution
4. Build user profile aggregation
5. Test cross-session preference application
6. Monitor preference extraction accuracy
7. Add preference management UI (optional)

Preference memory transforms your agent from stateless to personalised, creating unique experiences for each user.
