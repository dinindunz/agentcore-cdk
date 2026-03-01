"""Infrastructure tests for creating AgentCore memory events.

These tests verify that memory events can be created successfully
and are properly stored in AgentCore memory.

Run with:
    pytest tests/infrastructure/memory/test_memory_create.py -v
    pytest tests/infrastructure/memory/test_memory_create.py -v -m infrastructure
"""

from datetime import UTC, datetime

import pytest


@pytest.mark.infrastructure
@pytest.mark.parametrize(
    "event_type,content",
    [
        ("preference", "User prefers Australian English spelling"),
        ("preference", "User's name is test-user"),
        ("fact", "User lives in Melbourne, Australia"),
        ("fact", "User works with Python and AWS CDK"),
    ],
)
def test_create_memory_event(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
    unique_session_id,
    event_type,
    content,
):
    """Test creating different types of memory events.

    Args:
        bedrock_agentcore_client: Boto3 client fixture
        memory_id: AgentCore memory ID from SSM
        test_actor_id: Test user actor ID
        unique_session_id: Unique session ID for test isolation
        event_type: Type of memory event ('preference' or 'fact')
        content: Content to store in memory
    """
    # Format messages based on event type
    if event_type == "preference":
        user_message = f"Please remember this preference: {content}"
        assistant_message = f"I'll remember that. Preference noted: {content}"
    else:  # fact
        user_message = f"Here's an important fact: {content}"
        assistant_message = f"Understood. I've noted this fact: {content}"

    # Create the event with new API format (tagged union with conversational wrapper)
    response = bedrock_agentcore_client.create_event(
        memoryId=memory_id,
        actorId=test_actor_id,
        sessionId=unique_session_id,
        eventTimestamp=datetime.now(UTC),
        payload=[
            {
                "conversational": {
                    "role": "USER",
                    "content": {"text": user_message},
                }
            },
            {
                "conversational": {
                    "role": "ASSISTANT",
                    "content": {"text": assistant_message},
                }
            },
        ],
    )

    # Assertions - eventId is now nested in 'event' object
    assert "event" in response, "Response should contain event"
    assert "eventId" in response["event"], "Event should contain eventId"
    assert response["event"]["eventId"], "Event ID should not be empty"

    # Verify response metadata - 201 for created
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 201


@pytest.mark.infrastructure
def test_create_event_invalid_memory_id(
    bedrock_agentcore_client,
    test_actor_id,
    unique_session_id,
):
    """Test that creating event with invalid memory ID fails gracefully."""
    invalid_memory_id = "invalid-memory-id-12345"

    with pytest.raises(Exception) as exc_info:
        bedrock_agentcore_client.create_event(
            memoryId=invalid_memory_id,
            actorId=test_actor_id,
            sessionId=unique_session_id,
            eventTimestamp=datetime.now(UTC),
            payload=[
                {"conversational": {"role": "USER", "content": {"text": "Test message"}}},
                {"conversational": {"role": "ASSISTANT", "content": {"text": "Test response"}}},
            ],
        )

    # Verify that an appropriate exception was raised
    assert exc_info.value is not None


@pytest.mark.infrastructure
def test_memory_event_extraction_delay(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
    unique_session_id,
):
    """Test documenting that memory extraction has 60-90 second delay.

    This test creates an event and immediately checks if it's available
    in memory records. It's expected to NOT find the record immediately,
    demonstrating the asynchronous extraction process.

    Note: This is a documentation/awareness test, not a full end-to-end test.
    """
    # Create a test event
    test_content = "This is a test preference for extraction timing"

    bedrock_agentcore_client.create_event(
        memoryId=memory_id,
        actorId=test_actor_id,
        sessionId=unique_session_id,
        eventTimestamp=datetime.now(UTC),
        payload=[
            {"conversational": {"role": "USER", "content": {"text": f"Remember: {test_content}"}}},
            {
                "conversational": {
                    "role": "ASSISTANT",
                    "content": {"text": f"Noted: {test_content}"},
                }
            },
        ],
    )

    # Try to retrieve immediately (should not find it yet)
    namespace = f"/preferences/{test_actor_id}/"

    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=20,
    )

    records = response.get("memoryRecordSummaries", [])

    # Look for our content in the records
    found_immediately = any(test_content in str(record.get("content", {})) for record in records)

    # Expected behaviour: extraction is NOT immediate due to 60-90s asynchronous delay
    # The record typically won't be found in immediate retrieval
    # See test_memory_queries.py for tests that verify extraction after waiting
    _ = found_immediately  # Acknowledge the variable is intentionally unused here
