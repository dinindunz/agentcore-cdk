import json
import sys

from tests.common.auth import iam as auth

query = sys.argv[1] if len(sys.argv) > 1 else "add two numbers"

payload = {
    "jsonrpc": "2.0",
    "id": "search-tools-request",
    "method": "tools/call",
    "params": {
        "name": "x_amz_bedrock_agentcore_search",
        "arguments": {
            "query": query,
        },
    },
}

print(f"Searching IAM Gateway at: {auth.get_gateway_url()}")
print(f"Query: {query}\n")

status_code, response_data = auth.make_request(payload, include_event_stream=False)
if status_code == 200:
    print(json.dumps(response_data, indent=2))
else:
    print(f"HTTP {status_code}: {response_data}")
