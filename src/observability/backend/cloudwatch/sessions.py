"""Session extraction from CloudWatch Logs."""

from collections import defaultdict
from typing import Any

from ..config import Config
from ..models import Session, Trace
from .cache import run_cached_query
from .spans import build_trace_from_spans, parse_span, run_cloudwatch_query


def query_sessions(
    agent_log_group: str, hours: int = 24, region: str | None = None
) -> list[Session]:
    """Extract sessions from agent's CloudWatch log group.

    Args:
        agent_log_group: Agent's log group to query
        hours: Hours to look back (default 24)
        region: AWS region (defaults to Config.AWS_REGION)

    Returns:
        List of Session objects with aggregated traces
    """
    if region is None:
        region = Config.AWS_REGION

    # Query agent's log group for OTEL logs
    query = """
    fields @timestamp, @message
    | filter @logStream = "otel-rt-logs"
    | sort @timestamp asc
    | limit 1000
    """

    # Use cached query execution
    def _query():
        return run_cloudwatch_query(agent_log_group, query, hours, region)

    results = run_cached_query(_query)

    # Parse OTEL logs from @message field
    import json

    # Group by (trace_id, span_id) to deduplicate
    span_events: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    trace_metadata: dict[str, dict[str, Any]] = {}

    for record in results:
        # Extract fields
        fields = {field["field"]: field["value"] for field in record}

        # Parse @message JSON
        message_str = fields.get("@message", "{}")
        try:
            message = json.loads(message_str)
        except (json.JSONDecodeError, ValueError):
            continue

        # Extract trace and span IDs
        trace_id = message.get("traceId")
        span_id = message.get("spanId")

        if not trace_id or not span_id:
            continue

        # Extract scope and attributes
        scope = message.get("scope", {})
        scope_name = scope.get("name", "")
        attributes = message.get("attributes", {})

        # Check body for additional context
        body = message.get("body", {})
        if isinstance(body, dict):
            attributes.update(body)

        # Extract event name
        event_name = attributes.get("event.name", "")

        # Determine span name from event type or scope
        span_name = "unknown"
        if event_name == "gen_ai.system.message":
            span_name = "System Prompt"
        elif event_name == "gen_ai.user.message":
            span_name = "User Message"
        elif event_name == "gen_ai.choice":
            span_name = "LLM Response"
        elif event_name == "gen_ai.tool.message":
            span_name = "Tool Execution"
        elif event_name == "gen_ai.assistant.message":
            span_name = "Assistant Message"
        elif scope_name:
            # Use scope name as fallback
            span_name = scope_name.split(".")[-1].replace("_", " ").title()

        session_id = (
            attributes.get("session.id")
            or attributes.get("sessionId")
            or attributes.get("strands.session_id")
        )
        actor_id = (
            attributes.get("actor.id")
            or attributes.get("actorId")
            or attributes.get("strands.actor_id")
            or "unknown"
        )

        # Skip if no session ID
        if not session_id:
            continue

        # Store trace metadata
        if trace_id not in trace_metadata:
            trace_metadata[trace_id] = {
                "session_id": session_id,
                "actor_id": actor_id,
                "timestamp": fields.get("@timestamp"),
            }

        # Group events by (trace_id, span_id) for deduplication
        span_key = (trace_id, span_id)
        span_events[span_key].append(
            {
                "message": message,
                "attributes": attributes,
                "scope": scope,
                "event_name": event_name,
                "span_name": span_name,
            }
        )

    # Deduplicate and merge span events by spanId
    traces_map: dict[str, list] = defaultdict(list)
    for (trace_id, span_id), events in span_events.items():
        # Merge attributes from all events with same spanId
        merged_attributes = {}
        merged_message = {}
        span_name = "unknown"
        event_name = ""

        for event in events:
            # Merge attributes (later events override earlier ones)
            merged_attributes.update(event["attributes"])
            # Keep message data
            msg = event["message"]
            if msg.get("timeUnixNano", 0) > merged_message.get("timeUnixNano", 0):
                merged_message = msg
            # Prefer strands.telemetry.tracer event names
            if event["event_name"] == "strands.telemetry.tracer" or not event_name:
                event_name = event["event_name"]
                span_name = event["span_name"]

        # Create consolidated span record
        span_record = {
            "spanId": span_id,
            "traceId": trace_id,
            "parentSpanId": merged_message.get("parentSpanId"),
            "name": span_name,
            "kind": merged_message.get("kind", "INTERNAL"),
            "attributes": merged_attributes,
            "scope": events[0]["scope"],
            "event_name": event_name,
            "timeUnixNano": merged_message.get("timeUnixNano", 0),
            "endTimeUnixNano": merged_message.get("endTimeUnixNano", 0),
            "events": merged_message.get("events", []),
        }

        # Convert to CloudWatch Logs Insights result format for parse_span
        formatted_record = [{"field": k, "value": v} for k, v in span_record.items()]
        traces_map[trace_id].append(formatted_record)

    # Build Trace objects from spans
    traces: list[Trace] = []
    for trace_id, span_records in traces_map.items():
        metadata = trace_metadata.get(trace_id, {})
        session_id = metadata.get("session_id", "unknown")
        actor_id = metadata.get("actor_id", "unknown")

        # Parse spans
        spans = [parse_span(record) for record in span_records]

        # Build trace
        trace = build_trace_from_spans(trace_id, session_id, actor_id, spans)
        traces.append(trace)

    # Group traces by session ID
    sessions_map: dict[str, list[Trace]] = defaultdict(list)
    for trace in traces:
        sessions_map[trace.session_id].append(trace)

    # Build Session objects
    sessions: list[Session] = []
    for session_id, session_traces in sessions_map.items():
        if not session_traces:
            continue

        # Sort traces by start time
        session_traces.sort(key=lambda t: t.start_time)

        # Get actor ID and agent name from first trace
        actor_id = session_traces[0].actor_id
        agent_name = _extract_agent_name(agent_log_group)

        # Calculate session timing
        first_interaction = session_traces[0].start_time
        last_interaction = session_traces[-1].end_time

        # Aggregate metrics
        total_llm_calls = sum(t.total_llm_calls for t in session_traces)
        total_tool_calls = sum(t.total_tool_calls for t in session_traces)
        total_tokens = sum(t.total_input_tokens + t.total_output_tokens for t in session_traces)

        session = Session(
            session_id=session_id,
            actor_id=actor_id,
            agent_name=agent_name,
            first_interaction=first_interaction,
            last_interaction=last_interaction,
            traces=session_traces,
            trace_count=len(session_traces),
            total_llm_calls=total_llm_calls,
            total_tool_calls=total_tool_calls,
            total_tokens=total_tokens,
        )
        sessions.append(session)

    # Sort sessions by last interaction (most recent first)
    sessions.sort(key=lambda s: s.last_interaction, reverse=True)

    return sessions


def query_trace(
    trace_id: str, agent_log_group: str | None = None, hours: int = 48, region: str | None = None
) -> Trace:
    """Fetch detailed trace with all spans.

    Args:
        trace_id: Trace identifier
        agent_log_group: Agent's log group (if known, otherwise searches all)
        hours: Hours to look back (default 48 for older traces)
        region: AWS region (defaults to Config.AWS_REGION)

    Returns:
        Trace object with all spans

    Raises:
        ValueError: If trace not found
    """
    if region is None:
        region = Config.AWS_REGION

    import json

    import boto3

    # If no agent log group provided, find all agent log groups
    log_groups_to_search = []
    if agent_log_group:
        log_groups_to_search = [agent_log_group]
    else:
        # Discover all agent log groups
        logs_client = boto3.client("logs", region_name=region)
        response = logs_client.describe_log_groups(logGroupNamePrefix=Config.RUNTIME_LOG_PREFIX)
        log_groups_to_search = [lg["logGroupName"] for lg in response.get("logGroups", [])]

    # Query each log group for the trace
    all_results = []
    for log_group in log_groups_to_search:
        query = """
        fields @timestamp, @message
        | filter @logStream = "otel-rt-logs"
        | sort @timestamp asc
        | limit 1000
        """

        try:
            results = run_cloudwatch_query(log_group, query, hours, region)

            # Filter results for matching trace_id
            for record in results:
                fields = {field["field"]: field["value"] for field in record}
                message_str = fields.get("@message", "{}")
                try:
                    message = json.loads(message_str)
                    if message.get("traceId") == trace_id:
                        all_results.append(record)
                except (json.JSONDecodeError, ValueError):
                    continue

            # If we found results, no need to check other log groups
            if all_results:
                break
        except Exception:
            # Skip log groups that fail to query
            continue

    if not all_results:
        raise ValueError(f"Trace not found: {trace_id}")

    # Parse @message field to extract spans
    import json

    # Group by span_id to deduplicate
    span_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    session_id = "unknown"
    actor_id = "unknown"

    for record in all_results:
        fields = {field["field"]: field["value"] for field in record}
        message_str = fields.get("@message", "{}")

        try:
            message = json.loads(message_str)
        except (json.JSONDecodeError, ValueError):
            continue

        # Extract scope and attributes
        scope = message.get("scope", {})
        scope_name = scope.get("name", "")
        attributes = message.get("attributes", {})
        body = message.get("body", {})
        if isinstance(body, dict):
            attributes.update(body)

        # Extract event name
        event_name = attributes.get("event.name", "")

        # Determine span name from event type or scope
        span_name = "unknown"
        if event_name == "gen_ai.system.message":
            span_name = "System Prompt"
        elif event_name == "gen_ai.user.message":
            span_name = "User Message"
        elif event_name == "gen_ai.choice":
            span_name = "LLM Response"
        elif event_name == "gen_ai.tool.message":
            span_name = "Tool Execution"
        elif event_name == "gen_ai.assistant.message":
            span_name = "Assistant Message"
        elif scope_name:
            span_name = scope_name.split(".")[-1].replace("_", " ").title()

        # Update session/actor if found
        if session_id == "unknown":
            session_id = (
                attributes.get("session.id")
                or attributes.get("sessionId")
                or attributes.get("strands.session_id")
                or "unknown"
            )
        if actor_id == "unknown":
            actor_id = (
                attributes.get("actor.id")
                or attributes.get("actorId")
                or attributes.get("strands.actor_id")
                or "unknown"
            )

        # Group events by spanId for deduplication
        span_id = message.get("spanId", "")
        span_events[span_id].append(
            {
                "message": message,
                "attributes": attributes,
                "scope": scope,
                "event_name": event_name,
                "span_name": span_name,
            }
        )

    # Deduplicate and merge span events by spanId
    spans = []
    for span_id, events in span_events.items():
        # Merge attributes from all events with same spanId
        merged_attributes = {}
        merged_message = {}
        span_name = "unknown"
        event_name = ""

        for event in events:
            # Merge attributes (later events override earlier ones)
            merged_attributes.update(event["attributes"])
            # Keep message data from most recent event
            msg = event["message"]
            if msg.get("timeUnixNano", 0) > merged_message.get("timeUnixNano", 0):
                merged_message = msg
            # Prefer strands.telemetry.tracer event names
            if event["event_name"] == "strands.telemetry.tracer" or not event_name:
                event_name = event["event_name"]
                span_name = event["span_name"]

        # Create consolidated span record
        span_record = {
            "spanId": span_id,
            "traceId": merged_message.get("traceId", ""),
            "parentSpanId": merged_message.get("parentSpanId"),
            "name": span_name,
            "kind": merged_message.get("kind", "INTERNAL"),
            "attributes": merged_attributes,
            "scope": events[0]["scope"],
            "event_name": event_name,
            "timeUnixNano": merged_message.get("timeUnixNano", 0),
            "endTimeUnixNano": merged_message.get("endTimeUnixNano", 0),
            "events": merged_message.get("events", []),
        }

        # Convert to CloudWatch format for parse_span
        formatted_record = [{"field": k, "value": v} for k, v in span_record.items()]
        span = parse_span(formatted_record)
        spans.append(span)

    # Build trace
    trace = build_trace_from_spans(trace_id, session_id, actor_id, spans)

    return trace


def _extract_agent_name(log_group: str) -> str:
    """Extract agent name from log group path.

    Args:
        log_group: CloudWatch log group name

    Returns:
        Agent name
    """
    import re

    match = re.search(r"/runtimes/([^/]+)", log_group)
    if match:
        return match.group(1)
    return "unknown"
