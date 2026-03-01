"""Agent discovery API route."""

from flask import Blueprint, jsonify

from ..cloudwatch.agents import discover_agents
from ..config import Config

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/api/agents", methods=["GET"])
def get_agents():
    """List discovered AgentCore runtimes.

    Returns:
        JSON response with list of agents
    """
    try:
        agents = discover_agents(Config.AWS_REGION)

        return jsonify(
            {
                "agents": [
                    {
                        "name": agent.name,
                        "logGroup": agent.log_group,
                        "lastActivity": agent.last_activity.isoformat(),
                    }
                    for agent in agents
                ]
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
