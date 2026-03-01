"""Sessions query API route."""

from flask import Blueprint, jsonify, request

from ..cloudwatch.sessions import query_sessions
from ..config import Config

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/api/sessions", methods=["GET"])
def get_sessions():
    """Query sessions for an agent.

    Query parameters:
        agent: Agent log group name (required)
        hours: Lookback window in hours (default: 24)
        limit: Max sessions to return (default: 100)

    Returns:
        JSON response with list of sessions and their traces
    """
    # Get query parameters
    agent_log_group = request.args.get("agent")
    if not agent_log_group:
        return jsonify({"error": "Missing 'agent' parameter"}), 400

    try:
        hours = int(request.args.get("hours", Config.DEFAULT_HOURS))
    except ValueError:
        return jsonify({"error": "Invalid 'hours' parameter"}), 400

    try:
        limit = int(request.args.get("limit", Config.MAX_SESSIONS))
    except ValueError:
        return jsonify({"error": "Invalid 'limit' parameter"}), 400

    # Query sessions
    try:
        sessions = query_sessions(agent_log_group, hours, Config.AWS_REGION)

        # Apply limit
        sessions = sessions[:limit]

        # Convert to JSON-serialisable format
        return jsonify({"sessions": [session.to_dict() for session in sessions]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
