"""Short-term memory client for AgentCore."""

from datetime import datetime

import boto3


class ShortTermMemory:
    """Manages short-term conversation memory."""

    def __init__(self, memory_id: str, region_name: str):
        self.memory_id = memory_id
        self.data_client = boto3.client("bedrock-agentcore", region_name=region_name)

    def create_event(
        self,
        actor_id: str,
        session_id: str,
        messages: list[tuple[str, str]],
    ) -> dict:
        """
        Store conversation turn immediately.

        Args:
            actor_id: User identifier
            session_id: Session identifier
            messages: List of (content, role) tuples. Role can be USER, ASSISTANT, or TOOL

        Returns:
            Response from CreateEvent API
        """
        payload = []
        for content, role in messages:
            payload.append({"conversational": {"role": role, "content": {"text": content}}})

        print(f"[Memory] CreateEvent: actor={actor_id}, session={session_id}")
        response = self.data_client.create_event(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            eventTimestamp=datetime.now(),
            payload=payload,
        )
        print("[Memory] Event stored")
        return response

    def get_recent_context(
        self,
        actor_id: str,
        session_id: str,
        max_turns: int = 10,
    ) -> list[dict]:
        """
        Retrieve recent conversation history for context.

        Args:
            actor_id: User identifier
            session_id: Session identifier
            max_turns: Maximum number of events to retrieve

        Returns:
            List of events in chronological order
        """
        print(f"[Memory] ListEvents: actor={actor_id}, session={session_id}, max={max_turns}")
        response = self.data_client.list_events(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            maxResults=max_turns,
        )
        events = list(reversed(response.get("events", [])))
        print(f"[Memory] Retrieved {len(events)} events")
        return events
