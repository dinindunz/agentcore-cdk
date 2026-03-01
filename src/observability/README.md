# AgentCore Observability Dashboard

A web-based observability tool for monitoring and analysing AgentCore agent executions. Built with Flask backend and React + AWS Cloudscape Design System frontend.

## Features

- **Agent Discovery**: Automatically discovers AgentCore runtimes from CloudWatch log groups
- **Session Management**: Tracks conversation sessions with actors across multiple traces
- **Trace Visualisation**: Displays detailed trace information with span hierarchies
- **Tool Call Analysis**: Displays tool invocations with input parameters and outputs
- **Real-time Queries**: Fetches data from CloudWatch Logs Insights with 15-minute caching

## Architecture

```
src/observability/
├── backend/           # Flask REST API
│   ├── app.py         # Main Flask application
│   ├── config.py      # Configuration management (loads from root .env)
│   ├── models.py      # Data models (Agent, Span, Trace, Session)
│   ├── cloudwatch/    # CloudWatch Logs query modules
│   │   ├── agents.py   # Agent discovery
│   │   ├── sessions.py # Session extraction
│   │   ├── spans.py    # OTEL span parsing and deduplication
│   │   └── cache.py    # Query caching (15-min TTL)
│   └── routes/        # API endpoints
│       ├── agents.py   # GET /api/agents
│       ├── sessions.py # GET /api/sessions
│       └── traces.py   # GET /api/traces/:traceId
│
├── frontend/          # React + TypeScript application
│   ├── src/
│   │   ├── api/       # Backend API client
│   │   ├── components/ # Reusable UI components (TraceTree, SpanDetails)
│   │   ├── pages/      # Dashboard and TraceView pages
│   │   └── types/      # TypeScript type definitions
│   ├── dist/          # Built frontend (gitignored, auto-generated)
│   └── package.json
│
└── run.py             # Startup script
```

## Prerequisites

**This assumes you've already completed the project setup from the main README:**
- ✅ Python 3.12+ environment set up
- ✅ Dependencies installed (`pip install -e .`)
- ✅ AWS credentials configured
- ✅ `.env` file created from `.env.example`

If not, follow the setup instructions in the [main project README](../../README.md) first.

The observability dashboard dependencies (Flask, React, etc.) are automatically installed during project setup.

## Usage

### Quick Start

From the project root, use the Makefile commands:

```bash
# Install frontend dependencies
make observability-frontend-install

# Build the React frontend
make observability-frontend-build

# Launch the dashboard
make observability-dashboard
```

The dashboard starts on `http://localhost:5000` and automatically opens in your browser.


## How It Works

### Data Flow

1. **Agent Discovery**: Queries CloudWatch for log groups matching `/aws/bedrock-agentcore/runtimes/*`
2. **Session Extraction**: Queries `aws/spans` log group for OpenTelemetry traces
3. **Span Parsing**: Parses OTEL attributes (`gen_ai.*`, `tool.*`, etc.)
4. **Aggregation**: Groups spans into traces, traces into sessions
5. **Caching**: 15-minute TTL cache reduces CloudWatch query costs

### OpenTelemetry Attributes Parsed

**LLM Spans:**
- `gen_ai.request.model` - Model ID (e.g., "claude-sonnet-4-5")
- `gen_ai.usage.input_tokens` - Input token count
- `gen_ai.usage.output_tokens` - Output token count
- `gen_ai.request.temperature` - Generation temperature
- `gen_ai.user.message` / `input.value` - User input
- `gen_ai.assistant.message` / `output.value` - Assistant response

**Tool Spans:**
- `tool.name` - Tool identifier
- `tool.input` - Tool parameters (JSON)
- `tool.output` - Tool result (JSON)

**Session Spans:**
- `session.id` / `attributes.sessionId` - Session identifier
- `actor.id` / `attributes.actorId` - User/actor identifier

### CloudWatch Query Patterns

**Session Query** (from `cloudwatch/sessions.py`):

```sql
fields @timestamp, traceId, spanId, parentSpanId, name, kind,
       attributes, timeUnixNano, endTimeUnixNano, events
| filter ispresent(attributes.`session.id`) or ispresent(attributes.sessionId)
| sort @timestamp desc
| limit 1000
```

**Trace Query** (from `cloudwatch/sessions.py`):

```sql
fields @timestamp, traceId, spanId, parentSpanId, name, kind,
       attributes, timeUnixNano, endTimeUnixNano, events
| filter traceId = "{trace_id}"
| sort timeUnixNano asc
```

## API Endpoints

### GET /api/health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "region": "ap-southeast-2"
}
```

### GET /api/agents

List discovered AgentCore runtimes.

**Response:**

```json
{
  "agents": [
    {
      "name": "agent-core-stack-dev_agent_runtime",
      "logGroup": "/aws/bedrock-agentcore/runtimes/...",
      "lastActivity": "2024-02-24T10:30:00"
    }
  ]
}
```

### GET /api/sessions

Query sessions for an agent.

**Query Parameters:**
- `agent` (required): Agent log group name
- `hours` (optional, default: 24): Lookback window in hours
- `limit` (optional, default: 100): Max sessions to return

**Response:**

```json
{
  "sessions": [
    {
      "sessionId": "sess-123",
      "actorId": "user-456",
      "agentName": "agent-core-stack-dev_agent_runtime",
      "firstInteraction": "2024-02-24T10:00:00",
      "lastInteraction": "2024-02-24T10:30:00",
      "traceCount": 5,
      "totalLlmCalls": 10,
      "totalToolCalls": 3,
      "totalTokens": 1500,
      "traces": [...]
    }
  ]
}
```

### GET /api/traces/:traceId

Get detailed trace with all spans.

**Response:**

```json
{
  "trace": {
    "traceId": "trace-789",
    "sessionId": "sess-123",
    "actorId": "user-456",
    "startTime": "2024-02-24T10:15:00",
    "endTime": "2024-02-24T10:15:05",
    "durationMs": 5000,
    "totalLlmCalls": 2,
    "totalToolCalls": 1,
    "totalInputTokens": 500,
    "totalOutputTokens": 300,
    "userInput": "What is the weather?",
    "assistantOutput": "The weather is sunny.",
    "spans": [...]
  }
}
```

## Development

### Adding New Span Types

Edit `backend/cloudwatch/spans.py`:

```python
def parse_span(record: dict[str, Any]) -> Span:
    # Add new span type detection
    if "custom.attribute" in attributes:
        span_type = "custom"

    # Extract custom attributes
    custom_value = attributes.get("custom.attribute")
```

### Customising UI

Cloudscape components in `frontend/src/components/` and `frontend/src/pages/`.

Refer to [Cloudscape Design System docs](https://cloudscape.design/components/).
