"""Flask application for AgentCore Observability Dashboard."""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import Config
from .routes.agents import agents_bp
from .routes.sessions import sessions_bp
from .routes.traces import traces_bp

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for React development server
CORS(app)

# Register blueprints
app.register_blueprint(agents_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(traces_bp)

# Get frontend build directory
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


# ============================================================================
# API Routes
# ============================================================================


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "region": Config.AWS_REGION})


# ============================================================================
# Frontend Routes (Serve React App)
# ============================================================================


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve React frontend from dist directory."""
    # Check if frontend build exists
    if not FRONTEND_DIST.exists():
        return jsonify(
            {
                "error": "Frontend not built",
                "message": "Run 'make observability-frontend-build' to build the frontend",
            }
        ), 404

    # Serve static files
    if path and (FRONTEND_DIST / path).exists():
        return send_from_directory(str(FRONTEND_DIST), path)

    # Serve index.html for all other routes (SPA routing)
    return send_from_directory(str(FRONTEND_DIST), "index.html")


# ============================================================================
# Error Handlers
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
    )
