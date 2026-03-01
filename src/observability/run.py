#!/usr/bin/env python3
"""AgentCore Observability Dashboard launcher."""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


def open_browser(url: str, delay: float = 1.5):
    """Open browser after server starts.

    Args:
        url: URL to open
        delay: Seconds to wait before opening browser
    """
    time.sleep(delay)
    webbrowser.open(url)


def main():
    """Launch observability dashboard."""
    # Configuration
    port = int(os.getenv("OBSERVABILITY_PORT", 5000))
    auto_open = os.getenv("OBSERVABILITY_AUTO_OPEN", "true").lower() == "true"
    region = os.getenv("REGION_NAME", "ap-southeast-2")

    print("=" * 70)
    print("AgentCore Observability Dashboard")
    print("=" * 70)
    print(f"Region: {region}")
    print(f"Port: {port}")
    print(f"URL: http://localhost:{port}")
    print("=" * 70)
    print("\nStarting server...")

    # Auto-open browser
    if auto_open:
        threading.Thread(
            target=open_browser, args=(f"http://localhost:{port}",), daemon=True
        ).start()

    # Import Flask app (deferred to allow env vars to load)
    from backend.app import app

    # Run server
    try:
        app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
