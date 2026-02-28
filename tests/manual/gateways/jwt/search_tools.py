import json
import sys

from tests.common.auth import jwt as auth

query = sys.argv[1] if len(sys.argv) > 1 else "convert Celsius to Fahrenheit"

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

print(f"Searching JWT Gateway at: {auth.get_gateway_url()}")
print(f"Query: {query}\n")

response = auth.make_request(payload, include_event_stream=False)
print(json.dumps(response.json(), indent=2))
