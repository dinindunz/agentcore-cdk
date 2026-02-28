"""Example script to invoke a tool via IAM-authenticated gateway.

Usage:
    python invoke_tool.py <tool_name> <arguments_json>

Examples:
    python invoke_tool.py add '{"a": 5, "b": 3}'
    python invoke_tool.py temperature-converter___celsius_to_fahrenheit '{"celsius": 25}'
"""

import json
import sys

from tests.common.auth import iam as auth

if len(sys.argv) < 3:
    print("Usage: python invoke_tool.py <tool_name> <arguments_json>")
    print()
    print("Examples:")
    print('  python invoke_tool.py add \'{"a": 5, "b": 3}\'')
    print(
        "  python invoke_tool.py temperature-converter___celsius_to_fahrenheit '{\"celsius\": 25}'"
    )
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

print(f"Invoking tool via IAM Gateway: {auth.get_gateway_url()}")
print(f"Tool: {tool_name}")
print(f"Arguments: {json.dumps(arguments, indent=2)}\n")

status_code, response_data = auth.make_request(payload, include_event_stream=False)
if status_code == 200:
    print(json.dumps(response_data, indent=2))
else:
    print(f"HTTP {status_code}: {response_data}")
