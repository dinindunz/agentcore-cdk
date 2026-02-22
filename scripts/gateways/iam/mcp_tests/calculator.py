"""Test script to invoke calculator via IAM Gateway with SigV4 auth."""

import json

from .. import auth

# Call the add tool
call_tool_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "calculator___add",
        "arguments": {
            "a": 10,
            "b": 5,
        },
    },
}

print(f"Invoking IAM Gateway at: {auth.get_gateway_url()}")

print("\n=== Calling add tool (10 + 5) ===")
status_code, response_data = auth.make_request(call_tool_payload)
print(f"Status Code: {status_code}")
if status_code == 200:
    print(f"Response: {json.dumps(response_data, indent=2)}")
else:
    print(f"Response: {response_data}")
