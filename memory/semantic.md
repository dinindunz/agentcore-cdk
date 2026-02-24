# Semantic Memory

## What It Is

Semantic memory automatically **extracts facts, knowledge, and relationships** from conversations, building a persistent knowledge base about entities, concepts, and their connections. Unlike episodic memory (specific events) or summary memory (session overviews), semantic memory captures timeless factual information.

**Key Characteristics:**
- ✅ **Fact extraction** - Identifies objective information from conversations
- ✅ **Entity relationships** - Maps connections between concepts
- ✅ **User-scoped** - Knowledge persists across all sessions
- ✅ **Semantic search** - Query by concept, not keywords

## When to Use

Use semantic memory for:
- ✅ **Knowledge base building** - "User works on kubernetes projects"
- ✅ **Entity tracking** - "User's team uses React and Vue"
- ✅ **Domain knowledge** - "Anthropic builds Claude SDK"
- ✅ **Relationship mapping** - "kubernetes/kubernetes is the most popular k8s repo"
- ✅ **Persistent facts** - Information that doesn't change often

## Agent Code Implementation

### Memory Client

```python
from typing import List, Dict
import boto3


class SemanticMemory:
    """Manages semantic knowledge base for persistent facts."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def retrieve_facts(
        self,
        actor_id: str,
        query: str,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Retrieve facts using semantic search.

        Args:
            actor_id: User identifier
            query: Semantic query about facts/knowledge
            top_k: Number of fact records to return

        Returns:
            List of relevant fact records
        """
        response = self.data_client.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/semantic/actors/{actor_id}/",
            searchCriteria={"searchQuery": query},
            maxResults=top_k
        )
        return response.get('memoryRecordSummaries', [])

    def get_all_facts(
        self,
        actor_id: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """
        List all extracted facts for a user.

        Useful for building knowledge graphs or debugging.
        """
        response = self.data_client.list_memory_records(
            memoryId=self.memory_id,
            namespace=f"/strategies/semantic/actors/{actor_id}/",
            maxResults=max_results
        )
        return response.get('memoryRecordSummaries', [])

    def query_entity_relationships(
        self,
        actor_id: str,
        entity: str,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Query facts related to a specific entity.

        Args:
            actor_id: User identifier
            entity: Entity name (e.g., "kubernetes", "React", "Claude SDK")
            top_k: Number of related facts

        Returns:
            Facts mentioning or related to the entity
        """
        return self.retrieve_facts(
            actor_id=actor_id,
            query=f"Facts about {entity}",
            top_k=top_k
        )
```

### Integration with Agent

```python
# src/agent/main.py
from semantic_memory import SemanticMemory

semantic = SemanticMemory(
    memory_id=os.environ["MEMORY_ID"],
    region_name=os.environ["REGION_NAME"]
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", f"session_{uuid.uuid4()}")

    # 1. Extract entities from user message
    entities = extract_entities(user_message)  # e.g., ["kubernetes", "docker"]

    # 2. Query relevant facts for each entity
    fact_context = ""
    for entity in entities:
        facts = semantic.query_entity_relationships(
            actor_id=actor_id,
            entity=entity,
            top_k=5
        )

        if facts:
            fact_context += f"\n## Known Facts about {entity}:\n"
            for fact in facts:
                fact_context += f"- {fact.get('value', '')}\n"

    # 3. Enhance prompt with factual knowledge
    if fact_context:
        enhanced_prompt = f"{fact_context}\n## Current Request:\n{user_message}"
    else:
        enhanced_prompt = user_message

    # 4. Execute agent with knowledge base context
    result = agent(enhanced_prompt)
    response_text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )

    return {"result": response_text}

    # Note: Facts extracted automatically from CreateEvent (60+ sec delay)
```

## Namespace Pattern

### User-Level Facts
```
/strategies/semantic/actors/{actorId}/
```
**Always user-scoped** - Facts persist across all sessions

```
/strategies/semantic/actors/user-sarah-123/kubernetes-most-popular-109k-stars
/strategies/semantic/actors/user-sarah-123/user-works-on-cloud-native-projects
/strategies/semantic/actors/user-sarah-123/react-vs-vue-210k-vs-205k
/strategies/semantic/actors/user-sarah-123/claude-sdk-anthropic-repository
```

## Skill Examples

### Example 1: Repository Knowledge Building

**Session 1:**
```python
User: "Scout trending repos for 'kubernetes'"
Agent: "Kubernetes momentum: 138,632°F (top repo: kubernetes/kubernetes with 109k stars)"

# Facts extracted:
# - "kubernetes/kubernetes is the most popular kubernetes repository with 109,000 stars"
# - "kubernetes ecosystem has 50+ trending repositories"
# - "kubernetes trending momentum: 138,632°F"
```

**Session 2 (weeks later):**
```python
User: "What's the most popular kubernetes repo?"

# Agent queries semantic memory
facts = semantic.query_entity_relationships(
    actor_id="user123",
    entity="kubernetes"
)
# Retrieved: "kubernetes/kubernetes is the most popular with 109k stars"

Agent: "kubernetes/kubernetes is the most popular kubernetes repository (109,000 stars)" ✅
# Answered from knowledge base without re-executing search
```

**Session 3:**
```python
User: "Compare kubernetes and docker ecosystems"

# Agent queries facts for both entities
k8s_facts = semantic.query_entity_relationships(actor_id="user123", entity="kubernetes")
docker_facts = semantic.query_entity_relationships(actor_id="user123", entity="docker")

# Uses stored knowledge to provide instant comparison
Agent: "Based on previous analysis:
  - Kubernetes: Most popular repo 109k stars, momentum 138k°F
  - Docker: Most popular repo 78k stars, momentum 95k°F
  Kubernetes ecosystem is larger ✅"
```

### Example 2: Team/Project Context

**Session 1:**
```python
User: "Our team uses React for frontend and Python for backend"
Agent: "Got it! I'll remember that"

# Facts extracted:
# - "User's team uses React framework"
# - "User's team uses Python programming language"
# - "User's team tech stack: React (frontend), Python (backend)"
```

**Session 2:**
```python
User: "Find me trending repos"

# Agent queries facts about user's context
team_facts = semantic.retrieve_facts(
    actor_id="user123",
    query="user's team technology stack"
)
# Retrieved: "Team uses React and Python"

Agent: "Should I focus on React and Python repos (your team's stack)?" ✅
# Proactively applies contextual knowledge
```

**Session 3:**
```python
User: "Compare frontend frameworks"

# Agent uses team context
team_facts = semantic.retrieve_facts(actor_id="user123", query="frontend framework")
# Retrieved: "Team uses React"

Agent: "I'll compare React (your team's choice) with Vue and Angular" ✅
# Automatically includes relevant context
```

### Example 3: Domain Knowledge Accumulation

**Multiple Sessions - Learning about Ecosystem:**

**Session 1:**
```python
User: "Scout trending repos for 'kubernetes'"
# Fact: "kubernetes/kubernetes is the most popular k8s repo (109k stars)"
```

**Session 2:**
```python
User: "What's rancher/k3s?"
Agent: "It's a lightweight kubernetes distribution with 45k stars"
# Fact: "rancher/k3s is a lightweight kubernetes distribution (45k stars)"
```

**Session 3:**
```python
User: "Compare kubernetes distributions"

# Agent has accumulated knowledge about kubernetes ecosystem
k8s_facts = semantic.retrieve_facts(
    actor_id="user123",
    query="kubernetes distributions and repositories"
)

# Retrieved facts:
# - "kubernetes/kubernetes: 109k stars (main project)"
# - "rancher/k3s: 45k stars (lightweight distribution)"

Agent: "Based on what we know:
  1. kubernetes/kubernetes (109k stars) - Main Kubernetes project
  2. rancher/k3s (45k stars) - Lightweight distribution
  Want me to search for more distributions?" ✅
```

### Example 4: Skill Execution Tracking

**Session 1:**
```python
User: "Use trending topic scout for kubernetes"
Agent: [Executes skill successfully]

# Fact extracted:
# "trending_topic_scout skill successfully analysed kubernetes with result: 138k°F"
```

**Session 2:**
```python
User: "Use trending topic scout for python"
Agent: [Executes skill successfully]

# Fact extracted:
# "trending_topic_scout skill successfully analysed python with result: 112k°F"
```

**Session 3:**
```python
User: "Which skills have I used successfully?"

# Query semantic memory for skill usage
skill_facts = semantic.retrieve_facts(
    actor_id="user123",
    query="skill execution success"
)

# Retrieved:
# - "trending_topic_scout: successful on kubernetes"
# - "trending_topic_scout: successful on python"
# - "repo_comparison: successful on react vs vue"

Agent: "You've successfully used:
  1. trending_topic_scout (kubernetes, python)
  2. repo_comparison (react vs vue) ✅"
```

### Example 5: Entity Relationship Mapping

**Building Knowledge Graph:**

```python
# Session 1: Learn about Claude SDK
User: "What is anthropics/claude-sdk-python?"
Agent: "It's Anthropic's Python SDK for Claude with 4,200 stars"
# Facts:
# - "anthropics/claude-sdk-python is Anthropic's official Python SDK"
# - "claude-sdk-python has 4,200 stars"

# Session 2: Learn relationship
User: "Compare it with openai/openai-sdk"
Agent: "Claude SDK: 4.2k vs OpenAI SDK: 12.5k stars"
# Fact: "claude-sdk-python (4.2k stars) vs openai-sdk (12.5k stars) - OpenAI has 3x more"

# Session 3: Learn about parent entity
User: "Who builds Claude SDK?"
Agent: "Anthropic builds the Claude SDK"
# Fact: "Anthropic is the organisation behind claude-sdk-python"

# Session 4: Query relationships
User: "What do I know about Anthropic?"

relationships = semantic.query_entity_relationships(
    actor_id="user123",
    entity="Anthropic"
)

# Retrieved facts:
# - "Anthropic builds Claude SDK"
# - "Claude SDK: anthropics/claude-sdk-python"
# - "Claude SDK has 4.2k stars, growing vs OpenAI's 12.5k"

Agent: "What you know about Anthropic:
  - Builds Claude SDK (anthropics/claude-sdk-python)
  - Claude SDK has 4,200 stars
  - Currently smaller than OpenAI SDK (12.5k stars) but growing ✅"
```

## Evaluation Testing

### Test 1: Fact Extraction

```python
def test_fact_extraction():
    # Create conversation with factual information
    memory.create_event("test_user", "session_001", [
        ("kubernetes/kubernetes has 109,000 stars", "USER"),
        ("That's impressive! It's the most popular k8s repo", "ASSISTANT")
    ])

    # Wait for extraction
    time.sleep(70)

    # Query facts
    facts = semantic.retrieve_facts(
        actor_id="test_user",
        query="kubernetes repository stars"
    )

    # Validate fact extraction
    assert len(facts) > 0
    fact_text = str(facts[0]).lower()
    assert "kubernetes" in fact_text
    assert "109" in fact_text or "109000" in fact_text or "109,000" in fact_text
```

### Test 2: Knowledge Persistence

```python
def test_knowledge_persistence():
    # Session 1: Learn fact
    memory.create_event("test_user", "session_001", [
        ("Our team uses React", "USER"),
        ("Noted!", "ASSISTANT")
    ])
    time.sleep(70)

    # Session 2: Query fact (different session)
    facts = semantic.retrieve_facts(
        actor_id="test_user",
        query="team technology stack"
    )

    # Validate fact persists across sessions
    assert len(facts) > 0
    assert "react" in str(facts[0]).lower()
```

### Test 3: Entity Relationships

```python
def test_entity_relationships():
    # Build knowledge about entity
    memory.create_event("test_user", "session_001", [
        ("Claude SDK is built by Anthropic", "USER"),
        ("Yes, it's their official Python SDK", "ASSISTANT")
    ])

    memory.create_event("test_user", "session_002", [
        ("Claude SDK has 4,200 stars", "USER"),
        ("That's solid growth!", "ASSISTANT")
    ])

    time.sleep(70)

    # Query entity
    facts = semantic.query_entity_relationships(
        actor_id="test_user",
        entity="Claude SDK"
    )

    # Validate relationships captured
    assert len(facts) >= 2
    all_facts = " ".join([f.get('value', '') for f in facts]).lower()
    assert "anthropic" in all_facts
    assert "4200" in all_facts or "4,200" in all_facts
```

## Best Practices

### 1. Query Facts Before Answering Questions

```python
# Good: Check knowledge base first
if is_factual_question(user_message):
    facts = semantic.retrieve_facts(
        actor_id=actor_id,
        query=user_message,
        top_k=5
    )
    if facts:
        # Answer from knowledge base
        return build_answer_from_facts(facts)
    else:
        # Execute new search
        return execute_search()

# Bad: Always execute fresh search
return execute_search()  # ❌ Ignores stored knowledge
```

### 2. Build Entity Context

```python
def build_entity_context(actor_id: str, entities: List[str]) -> str:
    """Gather relevant facts for entities mentioned in request."""
    context = ""

    for entity in entities:
        facts = semantic.query_entity_relationships(
            actor_id=actor_id,
            entity=entity,
            top_k=5
        )

        if facts:
            context += f"\n## Known facts about {entity}:\n"
            for fact in facts:
                context += f"- {fact.get('value', '')}\n"

    return context
```

### 3. Track Skill Execution History

```python
# Store skill execution as facts
def record_skill_execution(skill_name: str, params: dict, result: str, success: bool):
    """Record skill execution facts for future reference."""
    fact_message = f"Skill {skill_name} with {params}: {result} (success: {success})"

    memory.create_event(
        actor_id=actor_id,
        session_id=session_id,
        messages=[
            (fact_message, "TOOL"),
            (f"Recorded: {skill_name} execution", "ASSISTANT")
        ]
    )
    # Fact will be extracted: "skill_name successfully/unsuccessfully executed with params..."
```

### 4. Deduplicate Facts

```python
# Before relying on facts, check for consistency
def get_deduplicated_facts(actor_id: str, query: str) -> List[str]:
    """Retrieve facts and resolve conflicts."""
    facts = semantic.retrieve_facts(actor_id, query, top_k=10)

    # Group by entity
    entity_facts = {}
    for fact in facts:
        entity = extract_entity(fact.get('value', ''))
        if entity not in entity_facts:
            entity_facts[entity] = []
        entity_facts[entity].append(fact)

    # Keep most recent fact per entity
    deduplicated = []
    for entity, fact_list in entity_facts.items():
        # Assume most recent is most accurate
        deduplicated.append(fact_list[0])

    return [f.get('value', '') for f in deduplicated]
```

## Common Fact Types

### Repository Facts
- "kubernetes/kubernetes has 109,000 stars"
- "react repository owned by facebook organisation"
- "vue is 5,000 stars behind react"

### Team/User Facts
- "User works on cloud-native projects"
- "User's team uses React and Python"
- "User focuses on kubernetes ecosystem"

### Tool/Skill Facts
- "trending_topic_scout works well for topics with 20+ repos"
- "calculator tools accurate for GitHub star arithmetic"
- "temperature_converter adds engaging presentation"

### Relationship Facts
- "Anthropic builds Claude SDK"
- "kubernetes/kubernetes is the main kubernetes project"
- "rancher/k3s is a lightweight kubernetes distribution"

## Performance Metrics

Track these metrics for semantic memory:
- **Fact extraction rate** - % of conversations that yield facts
- **Fact accuracy** - Correctness of extracted facts
- **Knowledge coverage** - Number of entities with facts
- **Query hit rate** - % of queries answered from knowledge base
- **Fact freshness** - How often facts are updated

## Limitations

- ❌ **60+ second delay** - Facts not available immediately
- ❌ **No fact updates** - New facts don't automatically override old ones
- ❌ **Extraction variability** - Same conversation may yield different facts
- ❌ **No explicit fact management** - Can't manually add/edit facts
- ❌ **Context required** - Facts extracted from conversations, not standalone statements

## When to Use Other Strategies

- **Need immediate context** → Use [short_term.md](./short_term.md)
- **Learning from experiences** → Use [episodic.md](./episodic.md)
- **Learning user preferences** → Use [preference.md](./preference.md)
- **Session summaries** → Use [summary.md](./summary.md)

## Knowledge Base Use Cases

### 1. Project Context Awareness
Build understanding of user's projects, teams, and domains over time

### 2. Entity Tracking
Maintain knowledge about repositories, organisations, technologies mentioned

### 3. Skill Performance Database
Track which skills work well for which use cases

### 4. Decision Knowledge
Remember technical decisions, comparisons, and rationales

### 5. Relationship Mapping
Build graph of connections between entities (Anthropic → Claude SDK → Python)

## Next Steps

1. Enable semantic strategy in CDK MemoryConstruct
2. Implement SemanticMemory client in `src/agent/memory/semantic.py`
3. Extract entities from user messages
4. Query facts before executing expensive operations
5. Test fact extraction accuracy
6. Build entity relationship queries
7. Monitor knowledge base growth
8. Create knowledge graph visualisation (optional)

Semantic memory transforms your agent from stateless to knowledgeable, building persistent understanding of your domain over time.
