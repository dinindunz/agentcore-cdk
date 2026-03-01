"""Data models for observability dashboard."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Agent:
    """Discovered AgentCore runtime."""

    name: str  # Runtime name (e.g., "agent-core-stack-dev_agent_runtime")
    log_group: str  # CloudWatch log group path
    last_activity: datetime  # Most recent log entry timestamp


@dataclass
class Span:
    """OpenTelemetry span representing a single operation."""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    name: str  # e.g., "llm.invoke", "tool.call"
    kind: str  # "INTERNAL", "CLIENT", etc.
    start_time: int  # Nanoseconds
    end_time: int
    duration_ms: float  # Calculated milliseconds

    # OpenTelemetry attributes (full dict)
    attributes: dict[str, Any] = field(default_factory=dict)

    # Parsed attribute shortcuts
    span_type: str = "other"  # "llm", "tool", "session", "other"

    # LLM-specific attributes
    llm_model: str | None = None
    llm_input_tokens: int | None = None
    llm_output_tokens: int | None = None
    llm_temperature: float | None = None

    # Tool-specific attributes
    tool_name: str | None = None
    tool_input: Any | None = None
    tool_output: Any | None = None

    # Message attributes
    user_message: str | None = None
    assistant_message: str | None = None

    # Strands telemetry attributes (for labeling)
    trigger_type: str | None = None  # "user" or "tool_result"
    finish_reason: str | None = None  # "end_turn" or "tool_use"

    # Events (e.g., streaming chunks)
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "spanId": self.span_id,
            "traceId": self.trace_id,
            "parentSpanId": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "durationMs": self.duration_ms,
            "spanType": self.span_type,
            # LLM attributes
            "llmModel": self.llm_model,
            "llmInputTokens": self.llm_input_tokens,
            "llmOutputTokens": self.llm_output_tokens,
            "llmTemperature": self.llm_temperature,
            # Tool attributes
            "toolName": self.tool_name,
            "toolInput": self.tool_input,
            "toolOutput": self.tool_output,
            # Messages
            "userMessage": self.user_message,
            "assistantMessage": self.assistant_message,
            # Strands telemetry attributes
            "triggerType": self.trigger_type,
            "finishReason": self.finish_reason,
            # Full attributes for debugging
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class Trace:
    """Collection of spans forming a single agent invocation."""

    trace_id: str
    session_id: str
    actor_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: float

    # Aggregated spans
    spans: list[Span] = field(default_factory=list)
    root_span: Span | None = None  # Top-level span

    # Aggregated metrics
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float | None = None  # If pricing data available

    # User interaction
    user_input: str | None = None
    assistant_output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "traceId": self.trace_id,
            "sessionId": self.session_id,
            "actorId": self.actor_id,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "durationMs": self.duration_ms,
            "totalLlmCalls": self.total_llm_calls,
            "totalToolCalls": self.total_tool_calls,
            "totalInputTokens": self.total_input_tokens,
            "totalOutputTokens": self.total_output_tokens,
            "totalCostUsd": self.total_cost_usd,
            "userInput": self.user_input,
            "assistantOutput": self.assistant_output,
            "spans": [span.to_dict() for span in self.spans],
        }


@dataclass
class Session:
    """Collection of traces for a single actor-session pair."""

    session_id: str
    actor_id: str
    agent_name: str
    first_interaction: datetime
    last_interaction: datetime

    # Traces in this session
    traces: list[Trace] = field(default_factory=list)
    trace_count: int = 0

    # Session-level aggregations
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "sessionId": self.session_id,
            "actorId": self.actor_id,
            "agentName": self.agent_name,
            "firstInteraction": self.first_interaction.isoformat(),
            "lastInteraction": self.last_interaction.isoformat(),
            "traceCount": self.trace_count,
            "totalLlmCalls": self.total_llm_calls,
            "totalToolCalls": self.total_tool_calls,
            "totalTokens": self.total_tokens,
            "traces": [trace.to_dict() for trace in self.traces],
        }
