"""Example script to invoke a tool via JWT-authenticated gateway.

Usage:
    python invoke_tool.py <tool_name> <arguments_json>

Examples:
    python invoke_tool.py temperature-converter___celsius_to_fahrenheit '{"celsius": 25}'
    python invoke_tool.py github___getAuthenticatedUser '{}'
"""

import json
import sys

import auth

if len(sys.argv) < 3:
    print("Usage: python invoke_tool.py <tool_name> <arguments_json>")
    print()
    print("Examples:")
    print(
        "  python invoke_tool.py temperature-converter___celsius_to_fahrenheit '{\"celsius\": 25}'"
    )
    print("  python invoke_tool.py github___getAuthenticatedUser '{}'")
    sys.exit(1)

tool_name = sys.argv[1]
arguments = json.loads(sys.argv[2])

payload = {
    "jsonrpc": "2.0",
    "id": "invoke-tool-request",
    "method": "tools/call",
    "params": {
        "name": tool_name,
        "arguments": arguments,
    },
}

print(f"Invoking tool via JWT Gateway: {auth.get_gateway_url()}")
print(f"Tool: {tool_name}")
print(f"Arguments: {json.dumps(arguments, indent=2)}\n")

response = auth.make_request(payload, include_event_stream=False)
print(json.dumps(response.json(), indent=2))
