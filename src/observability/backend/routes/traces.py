"""Trace detail API route."""

from flask import Blueprint, jsonify

from ..cloudwatch.sessions import query_trace
from ..config import Config

traces_bp = Blueprint("traces", __name__)


@traces_bp.route("/api/traces/<trace_id>", methods=["GET"])
def get_trace(trace_id: str):
    """Get detailed trace with all spans.

    Args:
        trace_id: Trace identifier from URL path

    Returns:
        JSON response with trace details and spans
    """
    try:
        trace = query_trace(trace_id, hours=48, region=Config.AWS_REGION)

        return jsonify({"trace": trace.to_dict()})
    except ValueError as e:
        # Trace not found
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
