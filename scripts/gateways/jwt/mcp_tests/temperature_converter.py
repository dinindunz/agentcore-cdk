"""Test script to invoke temperature converter via JWT Gateway."""

import json
import sys
from pathlib import Path

# Add parent directory to path to import auth module
sys.path.insert(0, str(Path(__file__).parent.parent))
import auth

# Call celsius_to_fahrenheit: 100°C → 212°F
celsius_to_fahrenheit_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "temperature-converter___celsius_to_fahrenheit",
        "arguments": {
            "celsius": 100,
        },
    },
}

# Call fahrenheit_to_celsius: 32°F → 0°C
fahrenheit_to_celsius_payload = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "temperature-converter___fahrenheit_to_celsius",
        "arguments": {
            "fahrenheit": 32,
        },
    },
}

print(f"Invoking JWT Gateway at: {auth.get_gateway_url()}")

print("\n=== Calling celsius_to_fahrenheit (100°C) ===")
response = auth.make_request(celsius_to_fahrenheit_payload, include_event_stream=False)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n=== Calling fahrenheit_to_celsius (32°F) ===")
response = auth.make_request(fahrenheit_to_celsius_payload, include_event_stream=False)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
