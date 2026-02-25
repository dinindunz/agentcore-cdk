# AgentCore Memory Strategies

This directory contains documentation for each memory type available in AWS Bedrock AgentCore.

## Memory Types Overview

| Memory Type | File | Purpose | Latency | Scope |
|------------|------|---------|---------|-------|
| **Short-Term** | [short_term.md](./short_term.md) | Raw conversation history within a session | Immediate | Session |
| **Episodic** | [episodic.md](./episodic.md) | Specific events with situation/intent/assessment | 60+ sec | Cross-session |
| **Summary** | [summary.md](./summary.md) | Condensed conversation overviews | 60+ sec | Session |
| **Preference** | [preference.md](./preference.md) | Learned user preferences and habits | 60+ sec | User |
| **Semantic** | [semantic.md](./semantic.md) | Facts, knowledge, and relationships | 60+ sec | User |

## Short-Term vs Long-Term

### Short-Term Memory
- **What**: Raw events stored via `CreateEvent`
- **When**: Immediate conversation context (last 5-10 turns)
- **Retrieval**: `ListEvents` API - synchronous
- **Example**: User says "Convert 100F to C" → Store exact message
- **Agent Usage**: Context for current session

### Long-Term Memory (All Strategies)
- **What**: Extracted insights from short-term events
- **When**: Cross-session knowledge and patterns
- **Retrieval**: `RetrieveMemoryRecords` API - semantic search
- **Processing**: Asynchronous (60+ seconds after event creation)
- **Agent Usage**: Learn from past interactions

## The Memory Flow

```
User Interaction
    ↓
CreateEvent
    ↓
Short-Term Memory (raw events)
    ↓ [Async Processing: 60+ seconds]
    ↓
Extraction Strategies:
    ├── Episodic → Episodes (situation, intent, assessment, reflection)
    ├── Summary → Session summaries
    ├── Preference → User preferences
    └── Semantic → Facts and knowledge
    ↓
Long-Term Memory (structured insights)
```

## Quick Reference: When to Use Which

### Use Short-Term Memory when:
- ✅ Need immediate conversation context
- ✅ Resolving "that", "it", "the previous one" references
- ✅ Multi-turn conversations within a session
- ✅ Can't wait 60+ seconds

### Use Episodic Memory when:
- ✅ Need to recall "what happened when..."
- ✅ Learning from past successes/failures
- ✅ Resuming interrupted workflows
- ✅ Identifying patterns across similar tasks

### Use Summary Memory when:
- ✅ Need conversation overviews
- ✅ Recapping previous sessions
- ✅ Understanding "what did we discuss about X?"
- ✅ Providing quick session context

### Use Preference Memory when:
- ✅ Personalising responses
- ✅ Learning user habits
- ✅ Proactively applying preferences
- ✅ Building user profiles

### Use Semantic Memory when:
- ✅ Building knowledge bases
- ✅ Extracting facts from conversations
- ✅ Tracking domain knowledge
- ✅ Creating persistent information stores

## Implementation Patterns

Each strategy file includes:
1. **What it is** - Definition and purpose
2. **When to use** - Specific use cases
3. **Agent code** - Implementation examples
4. **Namespace patterns** - How to organise data
5. **Skill examples** - Real usage with your AgentCore skills
6. **Evaluation testing** - How to validate effectiveness

## CDK Setup

For CDK infrastructure code (MemoryConstruct), see:
- `research/agentcore_memory.md` - Complete CDK patterns
- `research/memory_for_skills.md` - Integration with skills

## Next Steps

1. Read [short_term.md](./short_term.md) - Start with basic context retention
2. Read [episodic.md](./episodic.md) - Learn from past experiences
3. Read [preference.md](./preference.md) - Personalise agent behavior
4. Read [summary.md](./summary.md) - Enable session recaps
5. Read [semantic.md](./semantic.md) - Build knowledge bases

Start with short-term memory for immediate benefits, then add long-term strategies as needed.
