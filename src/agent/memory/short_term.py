"""Short-term memory client for AgentCore."""

from datetime import datetime

import boto3

from common.logger import logger


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

        logger.debug(
            f"[Memory] CreateEvent: actor={actor_id} session={session_id} messages={len(messages)}"
        )

        # Log message content at debug level
        for content, role in messages:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            logger.debug(f"[Memory] Storing message: role={role} content={content_preview}")

        response = self.data_client.create_event(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            eventTimestamp=datetime.now(),
            payload=payload,
        )

        event_id = response.get("eventId", "unknown")
        logger.debug(f"[Memory] Event stored: event_id={event_id}")
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
        logger.debug(f"[Memory] ListEvents: actor={actor_id} session={session_id} max={max_turns}")

        response = self.data_client.list_events(
            memoryId=self.memory_id,
            actorId=actor_id,
            sessionId=session_id,
            maxResults=max_turns,
        )

        events = list(reversed(response.get("events", [])))
        logger.debug(f"[Memory] Retrieved {len(events)} events")

        # Log event content at debug level
        for idx, event in enumerate(events, 1):
            event_id = event.get("eventId", "unknown")
            payload = event.get("payload", [])
            logger.debug(
                f"[Memory] Event {idx}/{len(events)}: event_id={event_id} turns={len(payload)}"
            )

            for turn in payload:
                if "conversational" in turn:
                    role = turn["conversational"]["role"]
                    text = turn["conversational"]["content"].get("text", "")
                    text_preview = text[:80] + "..." if len(text) > 80 else text
                    logger.debug(f"[Memory] Turn content: role={role} text={text_preview}")

        return events
