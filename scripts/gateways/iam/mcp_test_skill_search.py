"""Test script to invoke skill search via IAM Gateway with SigV4 auth."""

import json

import auth

# Search for "issue" related skills
search_payload_1 = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "skill-search___search_skills",
        "arguments": {
            "query": "issue",
        },
    },
}

print(f"Invoking IAM Gateway at: {auth.get_gateway_url()}")
print(f"Tool: skill-search___search_skills")
print(f"Query: 'issue'")

print("\n=== Calling skill-search___search_skills ===")
status_code, response_data = auth.make_request(search_payload_1)
print(f"Status Code: {status_code}")
print(f"Response:\n{json.dumps(response_data, indent=2)}")

# Try another search for "github stars"
search_payload_2 = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "skill-search___search_skills",
        "arguments": {
            "query": "github stars",
        },
    },
}

print("\n=== Calling skill-search___search_skills (query: 'github stars') ===")
status_code, response_data = auth.make_request(search_payload_2)
print(f"Status Code: {status_code}")
print(f"Response:\n{json.dumps(response_data, indent=2)}")
