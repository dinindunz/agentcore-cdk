"""OTEL span parsing from CloudWatch Logs."""

import json
from datetime import datetime
from typing import Any

import boto3

from ..config import Config
from ..models import Span, Trace


def parse_span(record: dict[str, Any]) -> Span:
    """Parse CloudWatch Logs record into Span object.

    Args:
        record: CloudWatch Logs Insights query result record

    Returns:
        Parsed Span object
    """
    # Extract fields from CloudWatch record format
    fields = {field["field"]: field["value"] for field in record}

    # Parse attributes (may be JSON string or dict)
    attributes_raw = fields.get("attributes", {})
    if isinstance(attributes_raw, str):
        try:
            attributes = json.loads(attributes_raw)
        except (json.JSONDecodeError, ValueError):
            attributes = {}
    else:
        attributes = attributes_raw if isinstance(attributes_raw, dict) else {}

    # Determine span type from attributes and event context
    span_type = "other"
    event_name = attributes.get("event.name", "")

    # Check if this is a strands telemetry event (agent execution trace)
    if event_name == "strands.telemetry.tracer":
        # This is an agent invocation span - check output for type
        # We'll determine if it's a tool call or LLM response based on finish_reason
        span_type = "session"  # Default to session until we parse the body
    elif "gen_ai.request.model" in attributes or "llm.model" in attributes:
        span_type = "llm"
    elif "tool.name" in attributes:
        span_type = "tool"
    elif "session.id" in attributes:
        span_type = "session"

    # Extract LLM-specific attributes
    llm_model = attributes.get("gen_ai.request.model") or attributes.get("llm.model")
    llm_input_tokens = attributes.get("gen_ai.usage.input_tokens") or attributes.get(
        "llm.usage.input_tokens"
    )
    llm_output_tokens = attributes.get("gen_ai.usage.output_tokens") or attributes.get(
        "llm.usage.output_tokens"
    )
    llm_temperature = attributes.get("gen_ai.request.temperature") or attributes.get(
        "llm.temperature"
    )

    # Extract tool-specific attributes
    tool_name = attributes.get("tool.name")
    tool_input_raw = attributes.get("tool.input")
    tool_output_raw = attributes.get("tool.output")

    # Parse tool input/output if JSON strings
    tool_input = None
    tool_output = None
    if tool_input_raw:
        if isinstance(tool_input_raw, str):
            try:
                tool_input = json.loads(tool_input_raw)
            except (json.JSONDecodeError, ValueError):
                tool_input = tool_input_raw
        else:
            tool_input = tool_input_raw

    if tool_output_raw:
        if isinstance(tool_output_raw, str):
            try:
                tool_output = json.loads(tool_output_raw)
            except (json.JSONDecodeError, ValueError):
                tool_output = tool_output_raw
        else:
            tool_output = tool_output_raw

    # Parse strands.telemetry.tracer body for trigger and interaction type
    trigger_type = None  # "user" or "tool_result"
    finish_reason = None  # "end_turn" or "tool_use"

    # Check if attributes contain input/output data (from strands telemetry events)
    if event_name == "strands.telemetry.tracer":
        # Extract input messages to determine trigger
        input_data = attributes.get("input", {})
        if isinstance(input_data, dict):
            input_msgs = input_data.get("messages", [])
            for msg in reversed(input_msgs):
                msg_role = msg.get("role")
                if msg_role in ["user", "tool_result"]:
                    trigger_type = msg_role
                    break

        # Extract output messages to determine finish reason
        output_data = attributes.get("output", {})
        if isinstance(output_data, dict):
            output_msgs = output_data.get("messages", [])
            for msg in output_msgs:
                if msg.get("role") == "assistant":
                    content = msg.get("content", {})
                    if isinstance(content, dict):
                        finish_reason = content.get("finish_reason")
                        # For tool_use, parse message JSON to get tool name
                        if finish_reason == "tool_use":
                            message_str = content.get("message", "")
                            if message_str:
                                try:
                                    message_data = json.loads(message_str)
                                    if isinstance(message_data, list) and len(message_data) > 0:
                                        tool_use_obj = message_data[0].get("toolUse", {})
                                        if isinstance(tool_use_obj, dict):
                                            tool_name = tool_use_obj.get("name")
                                except (json.JSONDecodeError, ValueError):
                                    pass
                        break

    # Extract message attributes
    user_message = attributes.get("gen_ai.user.message") or attributes.get("input.value")
    assistant_message = attributes.get("gen_ai.assistant.message") or attributes.get("output.value")

    # For strands telemetry events, extract messages from attributes
    if event_name == "strands.telemetry.tracer":
        input_data = attributes.get("input", {})
        output_data = attributes.get("output", {})

        if isinstance(input_data, dict):
            input_msgs = input_data.get("messages", [])
            # Get user message from last user/tool_result input
            for msg in reversed(input_msgs):
                if msg.get("role") == "user" and not user_message:
                    content = msg.get("content")
                    if isinstance(content, dict):
                        user_message = str(content.get("content", ""))
                    elif isinstance(content, str):
                        user_message = content
                    break

        if isinstance(output_data, dict):
            output_msgs = output_data.get("messages", [])
            # Get assistant message from output
            for msg in output_msgs:
                if msg.get("role") == "assistant" and not assistant_message:
                    content = msg.get("content", {})
                    if isinstance(content, dict):
                        assistant_message = content.get("message", "")
                    break

    # Parse timestamps
    start_ns = int(fields.get("timeUnixNano", 0))
    end_ns = int(fields.get("endTimeUnixNano", start_ns))

    # Calculate duration in milliseconds
    duration_ms = (end_ns - start_ns) / 1_000_000 if end_ns > start_ns else 0

    # Parse events
    events_raw = fields.get("events", [])
    if isinstance(events_raw, str):
        try:
            events = json.loads(events_raw)
        except (json.JSONDecodeError, ValueError):
            events = []
    else:
        events = events_raw if isinstance(events_raw, list) else []

    return Span(
        span_id=fields.get("spanId", ""),
        trace_id=fields.get("traceId", ""),
        parent_span_id=fields.get("parentSpanId"),
        name=fields.get("name", "unknown"),
        kind=fields.get("kind", "INTERNAL"),
        start_time=start_ns,
        end_time=end_ns,
        duration_ms=duration_ms,
        attributes=attributes,
        span_type=span_type,
        llm_model=llm_model,
        llm_input_tokens=int(llm_input_tokens) if llm_input_tokens else None,
        llm_output_tokens=int(llm_output_tokens) if llm_output_tokens else None,
        llm_temperature=float(llm_temperature) if llm_temperature else None,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        user_message=user_message,
        assistant_message=assistant_message,
        events=events,
        trigger_type=trigger_type,
        finish_reason=finish_reason,
    )


def build_trace_from_spans(
    trace_id: str, session_id: str, actor_id: str, spans: list[Span]
) -> Trace:
    """Build Trace object from list of spans.

    Args:
        trace_id: Trace identifier
        session_id: Session identifier
        actor_id: Actor identifier
        spans: List of parsed spans

    Returns:
        Constructed Trace object with aggregated metrics
    """
    if not spans:
        # Empty trace
        now = datetime.now()
        return Trace(
            trace_id=trace_id,
            session_id=session_id,
            actor_id=actor_id,
            start_time=now,
            end_time=now,
            duration_ms=0,
        )

    # Filter out incomplete spans (strands.telemetry.tracer events without finish_reason)
    # These are partial/intermediate events that don't represent complete interactions
    filtered_spans = []
    for span in spans:
        # Include all non-session spans
        if span.span_type != "session" or span.finish_reason:
            filtered_spans.append(span)
        # Skip session spans without finish_reason (incomplete/partial events)

    # Deduplicate similar spans - prefer spans with more complete data
    # When multiple spans have the same finish_reason and similar timing, keep the most complete one
    deduplicated_spans = []
    seen_contexts = set()

    # Sort by number of inputs (descending) and message format (plain text preferred)
    def span_score(s):
        # Higher score = more complete
        score = 0
        # Prefer spans with user_message and assistant_message
        if s.user_message:
            score += 10
        if s.assistant_message:
            score += 10
            # Prefer plain text over JSON format
            if not s.assistant_message.startswith("[{"):
                score += 5
        # Session spans get checked for input message count via attributes
        if s.span_type == "session" and "input" in s.attributes:
            input_data = s.attributes.get("input", {})
            if isinstance(input_data, dict):
                input_count = len(input_data.get("messages", []))
                score += input_count  # More inputs = more complete context
        return score

    sorted_filtered = sorted(filtered_spans, key=span_score, reverse=True)

    for span in sorted_filtered:
        # Create context key based on finish_reason and user message
        context_key = (span.finish_reason, span.user_message[:50] if span.user_message else "")
        if context_key not in seen_contexts:
            deduplicated_spans.append(span)
            seen_contexts.add(context_key)

    # Use deduplicated spans if any, otherwise use filtered, otherwise use all
    spans_to_use = (
        deduplicated_spans if deduplicated_spans else (filtered_spans if filtered_spans else spans)
    )

    # Sort spans by start time
    sorted_spans = sorted(spans_to_use, key=lambda s: s.start_time)

    # Find root span (no parent)
    root_span = next((s for s in sorted_spans if not s.parent_span_id), sorted_spans[0])

    # Calculate trace timing
    start_ns = min(s.start_time for s in sorted_spans)
    end_ns = max(s.end_time for s in sorted_spans)
    start_time = datetime.fromtimestamp(start_ns / 1_000_000_000)
    end_time = datetime.fromtimestamp(end_ns / 1_000_000_000)
    duration_ms = (end_ns - start_ns) / 1_000_000

    # Aggregate metrics
    total_llm_calls = sum(1 for s in sorted_spans if s.span_type == "llm")
    total_tool_calls = sum(1 for s in sorted_spans if s.span_type == "tool")
    total_input_tokens = sum(
        s.llm_input_tokens for s in sorted_spans if s.llm_input_tokens is not None
    )
    total_output_tokens = sum(
        s.llm_output_tokens for s in sorted_spans if s.llm_output_tokens is not None
    )

    # Extract user input and assistant output from root or session spans
    user_input = root_span.user_message
    assistant_output = root_span.assistant_message

    # If not in root, look for session-level spans
    if not user_input or not assistant_output:
        for span in sorted_spans:
            if span.span_type == "session":
                if not user_input and span.user_message:
                    user_input = span.user_message
                if not assistant_output and span.assistant_message:
                    assistant_output = span.assistant_message

    return Trace(
        trace_id=trace_id,
        session_id=session_id,
        actor_id=actor_id,
        start_time=start_time,
        end_time=end_time,
        duration_ms=duration_ms,
        spans=sorted_spans,
        root_span=root_span,
        total_llm_calls=total_llm_calls,
        total_tool_calls=total_tool_calls,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        user_input=user_input,
        assistant_output=assistant_output,
    )


def run_cloudwatch_query(
    log_group: str, query_string: str, hours: int, region: str | None = None
) -> list[dict[str, Any]]:
    """Execute CloudWatch Logs Insights query.

    Args:
        log_group: Log group to query
        query_string: CloudWatch Logs Insights query
        hours: Hours to look back
        region: AWS region (defaults to Config.AWS_REGION)

    Returns:
        List of query result records
    """
    if region is None:
        region = Config.AWS_REGION

    logs_client = boto3.client("logs", region_name=region)

    # Calculate time range
    from datetime import timedelta

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    # Start query
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int(start_time.timestamp()),
        endTime=int(end_time.timestamp()),
        queryString=query_string,
    )

    query_id = response["queryId"]

    # Poll for completion
    import time

    max_attempts = 60  # 30 seconds timeout
    for _ in range(max_attempts):
        result = logs_client.get_query_results(queryId=query_id)
        status = result["status"]

        if status in ["Complete", "Failed", "Cancelled"]:
            break

        time.sleep(0.5)

    # Return results
    if status == "Complete":
        return result.get("results", [])
    else:
        raise RuntimeError(f"CloudWatch query failed with status: {status}")
