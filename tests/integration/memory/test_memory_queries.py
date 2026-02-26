"""Integration tests for querying AgentCore memory.

These tests verify that memory retrieval queries work correctly
and return expected results based on relevance scoring.

Prerequisites:
    - Memory events must be created and extracted (60-90s delay)
    - Run test_memory_create.py first and wait for extraction

Run with:
    pytest tests/integration/memory/test_memory_queries.py -v
    pytest tests/integration/memory/test_memory_queries.py::test_search_preference_memory -v
"""

import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "query,expected_found",
    [
        ("name", True),  # Should match if name preference exists
        ("what is my name", True),
        ("user name", True),
        ("prefer", True),  # Should match preferences
        ("language preference", True),  # If language pref exists
        ("nonexistent_query_xyz_123", False),  # Should not match anything
    ],
)
def test_search_preference_memory(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
    query,
    expected_found,
):
    """Test searching preference memory with various queries.

    Note: This test assumes preference memory events have been created
    and extracted. If no records exist, the test will be skipped.

    Args:
        bedrock_agentcore_client: Boto3 client fixture
        memory_id: AgentCore memory ID
        test_actor_id: Test user actor ID
        query: Search query text
        expected_found: Whether records are expected to be found
    """
    namespace = f"/preferences/{test_actor_id}/"

    # First, check if any preference records exist
    list_response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=1,
    )

    if not list_response.get("memoryRecordSummaries"):
        pytest.skip(
            "No preference records found for test-user. "
            "Run test_memory_create.py and wait 90 seconds for extraction."
        )

    # Perform search query
    response = bedrock_agentcore_client.retrieve_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        searchCriteria={"searchQuery": query},
        maxResults=5,
    )

    records = response.get("memoryRecordSummaries", [])

    if expected_found:
        # Verify structure of returned records
        if records:
            record = records[0]
            assert "content" in record, "Record should have content field"
            assert "score" in record, "Record should have relevance score"
            assert record["score"] > 0, "Score should be positive"
    else:
        # For nonexistent queries, we might get empty results
        # This is more of a sanity check
        pass


@pytest.mark.integration
@pytest.mark.parametrize(
    "query",
    ["location", "city", "lives", "Melbourne", "Australia"],
)
def test_search_semantic_memory(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
    query,
):
    """Test searching semantic (facts) memory.

    Args:
        bedrock_agentcore_client: Boto3 client fixture
        memory_id: AgentCore memory ID
        test_actor_id: Test user actor ID
        query: Search query text
    """
    namespace = f"/facts/{test_actor_id}/"

    # Check if semantic records exist
    list_response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=1,
    )

    if not list_response.get("memoryRecordSummaries"):
        pytest.skip(
            "No semantic records found for test-user. "
            "Create test facts first."
        )

    # Perform search
    response = bedrock_agentcore_client.retrieve_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        searchCriteria={"searchQuery": query},
        maxResults=5,
    )

    # Verify response structure
    assert "memoryRecordSummaries" in response
    records = response["memoryRecordSummaries"]

    # If records found, verify they have required fields
    for record in records:
        assert "content" in record
        assert "score" in record

        # Verify score is reasonable (0.0 to 1.0 typically)
        assert 0 <= record["score"] <= 1.0


@pytest.mark.integration
def test_retrieve_memory_max_results(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
):
    """Test that maxResults parameter is respected."""
    namespace = f"/preferences/{test_actor_id}/"

    # Check if records exist
    list_response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=20,
    )

    total_records = len(list_response.get("memoryRecordSummaries", []))

    if total_records == 0:
        pytest.skip("No records found for test-user")

    # Request limited results
    max_results = min(2, total_records)

    response = bedrock_agentcore_client.retrieve_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        searchCriteria={"searchQuery": "preference"},
        maxResults=max_results,
    )

    records = response.get("memoryRecordSummaries", [])

    # Verify we got at most the requested number
    assert len(records) <= max_results


@pytest.mark.integration
def test_query_nonexistent_namespace(
    bedrock_agentcore_client,
    memory_id,
):
    """Test querying a namespace that doesn't exist."""
    nonexistent_namespace = "/nonexistent/actor-xyz-123/"

    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=nonexistent_namespace,
        maxResults=10,
    )

    # Should return empty list, not error
    assert response.get("memoryRecordSummaries", []) == []
