"""Test script to invoke GitHub MCP server via JWT Gateway."""

import json
import sys
from pathlib import Path

# Add parent directory to path to import auth module
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.common.auth import jwt as auth

# Get authenticated user
get_user_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "github___getAuthenticatedUser",
        "arguments": {},
    },
}

# List repos for the authenticated user
list_repos_payload = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "github___listAuthenticatedUserRepos",
        "arguments": {
            "sort": "updated",
            "per_page": 5,
        },
    },
}

# Search repositories
search_repos_payload = {
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
        "name": "github___searchRepositories",
        "arguments": {
            "q": "amazon-bedrock-agentcore language:python",
            "sort": "stars",
            "per_page": 5,
        },
    },
}

print(f"Invoking JWT Gateway at: {auth.get_gateway_url()}")

print("\n=== Get authenticated user ===")
response = auth.make_request(get_user_payload, include_event_stream=False)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n=== List repos (latest 5) ===")
response = auth.make_request(list_repos_payload, include_event_stream=False)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n=== Search repositories (amazon-bedrock-agentcore) ===")
response = auth.make_request(search_repos_payload, include_event_stream=False)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
