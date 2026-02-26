import json

import auth

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
}

print(f"JWT Gateway: {auth.get_gateway_url()}")

response = auth.make_request(payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
