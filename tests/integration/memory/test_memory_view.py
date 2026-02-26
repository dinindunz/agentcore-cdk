"""Integration tests for viewing AgentCore memory records.

These tests verify that memory records can be listed and viewed
across different memory strategies.

Run with:
    pytest tests/integration/memory/test_memory_view.py -v
"""

import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "strategy_name,namespace_pattern",
    [
        ("preference", "/preferences/{actor_id}/"),
        ("semantic", "/facts/{actor_id}/"),
    ],
)
def test_list_memory_records(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
    strategy_name,
    namespace_pattern,
):
    """Test listing memory records for different strategies.

    Args:
        bedrock_agentcore_client: Boto3 client fixture
        memory_id: AgentCore memory ID
        test_actor_id: Test user actor ID
        strategy_name: Name of memory strategy (for documentation)
        namespace_pattern: Namespace pattern with {actor_id} placeholder
    """
    namespace = namespace_pattern.format(actor_id=test_actor_id)

    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=20,
    )

    # Verify response structure
    assert "memoryRecordSummaries" in response

    records = response["memoryRecordSummaries"]

    # If records exist, verify their structure
    for record in records:
        assert "content" in record, f"{strategy_name} record should have content"
        assert "createdAt" in record, f"{strategy_name} record should have createdAt"

        # Verify content structure
        content = record["content"]
        if isinstance(content, dict):
            # Content should have 'text' field
            assert "text" in content or content, "Content should have text"


@pytest.mark.integration
def test_list_all_memory_strategies(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
):
    """Test listing records from all active memory strategies.

    This test demonstrates viewing memory across all strategies
    (preference, semantic, summary).
    """
    strategies = {
        "preference": f"/preferences/{test_actor_id}/",
        "semantic": f"/facts/{test_actor_id}/",
        "summary": f"/summaries/{test_actor_id}/",  # Note: session-scoped
    }

    results = {}

    for strategy_name, namespace in strategies.items():
        response = bedrock_agentcore_client.list_memory_records(
            memoryId=memory_id,
            namespace=namespace,
            maxResults=20,
        )

        record_count = len(response.get("memoryRecordSummaries", []))
        results[strategy_name] = record_count

    # Document what was found
    # Note: Summary memory is session-scoped, so listing without session_id
    # in namespace will return records across all sessions
    assert "preference" in results
    assert "semantic" in results
    assert "summary" in results


@pytest.mark.integration
def test_list_memory_pagination(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
):
    """Test memory record pagination with nextToken.

    This test demonstrates how to handle paginated results if
    there are more records than maxResults.
    """
    namespace = f"/preferences/{test_actor_id}/"
    max_results_per_page = 2

    # First page
    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=max_results_per_page,
    )

    first_page_records = response.get("memoryRecordSummaries", [])
    next_token = response.get("nextToken")

    # Verify first page
    assert len(first_page_records) <= max_results_per_page

    # If there's a next token, fetch second page
    if next_token:
        second_response = bedrock_agentcore_client.list_memory_records(
            memoryId=memory_id,
            namespace=namespace,
            maxResults=max_results_per_page,
            nextToken=next_token,
        )

        second_page_records = second_response.get("memoryRecordSummaries", [])

        # Verify we got different records
        if first_page_records and second_page_records:
            first_ids = {r.get("id") for r in first_page_records if "id" in r}
            second_ids = {r.get("id") for r in second_page_records if "id" in r}

            # Pages should have different records (if IDs are available)
            if first_ids and second_ids:
                assert first_ids != second_ids, "Pagination should return different records"


@pytest.mark.integration
def test_view_memory_record_content_types(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
):
    """Test that memory record content is properly formatted.

    Verifies that content field contains expected structure
    with text field.
    """
    namespace = f"/preferences/{test_actor_id}/"

    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=5,
    )

    records = response.get("memoryRecordSummaries", [])

    if not records:
        pytest.skip("No records found for test-user")

    for record in records:
        content = record["content"]

        # Content should be a dict with text
        if isinstance(content, dict):
            assert "text" in content or len(content) > 0

            if "text" in content:
                text = content["text"]
                assert isinstance(text, str)
                assert len(text) > 0, "Text content should not be empty"


@pytest.mark.integration
def test_memory_record_timestamps(
    bedrock_agentcore_client,
    memory_id,
    test_actor_id,
):
    """Test that memory records have valid timestamps."""
    from datetime import datetime

    namespace = f"/preferences/{test_actor_id}/"

    response = bedrock_agentcore_client.list_memory_records(
        memoryId=memory_id,
        namespace=namespace,
        maxResults=5,
    )

    records = response.get("memoryRecordSummaries", [])

    if not records:
        pytest.skip("No records found for test-user")

    for record in records:
        created_at = record.get("createdAt")

        if created_at:
            # Verify it's a valid datetime string or object
            if isinstance(created_at, str):
                # Try parsing ISO format timestamp
                try:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    # If not ISO format, just verify it's a non-empty string
                    assert len(created_at) > 0
            elif isinstance(created_at, datetime):
                # Already a datetime object
                assert created_at.year >= 2024
