# Common Authentication Modules

Shared authentication modules for AgentCore gateways and runtimes, used by both manual and infrastructure tests.

## Modules

### `iam.py` - IAM Gateway (SigV4 Auth)

Functions for IAM-authenticated gateway requests using AWS SigV4 signing.

```python
from tests.common.auth import iam

# Get gateway URL from SSM
url = iam.get_gateway_url()

# Get AWS credentials
credentials = iam.get_credentials()

# Get signed headers
headers = iam.get_signed_headers(url, payload_str)

# Make authenticated request
status_code, response = iam.make_request(payload)
```

### `jwt.py` - JWT Gateway (Cognito OAuth2)

Functions for JWT-authenticated gateway requests using Cognito client_credentials flow.

```python
from tests.common.auth import jwt

# Get gateway URL from SSM
url = jwt.get_gateway_url()

# Get OAuth2 access token from Cognito
token = jwt.get_access_token()

# Get authenticated headers
headers = jwt.get_headers()

# Make authenticated request
response = jwt.make_request(payload)
```

## Usage in Tests

**Manual tests:**
```python
from tests.common.auth import iam as auth
# or
from tests.common.auth import jwt as auth
```

**Infrastructure tests:**
```python
from tests.common.auth import iam as iam_auth
from tests.common.auth import jwt as jwt_auth
```

## Requirements

- `.env` file with `REGION_NAME`
- Deployed stack with SSM parameters and secrets
- Valid AWS credentials
