import json

import auth

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
}

print(f"IAM Gateway: {auth.get_gateway_url()}")

status_code, response_data = auth.make_request(payload)
print(f"Status Code: {status_code}")
print(f"Response: {json.dumps(response_data, indent=2)}")
