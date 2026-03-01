# OAuth Token Caching Configuration

This document explains how the agent runtime caches OAuth2 access tokens to reduce Cognito API calls and improve performance during conversational sessions.

## Overview

The agent runtime fetches OAuth2 access tokens from Cognito to authenticate with JWT-protected gateways. To optimise performance and respect API quotas, tokens are cached in memory and reused until they approach expiry.

## How It Works

### The Token Lifecycle

```
Time 0:00  → Token fetched from Cognito (expires at 15:00)
              Buffer = 90s (10% of 900s)
              Cache valid until 13:30 (15:00 - 90s)

Time 0:01  → get_access_token() → ✅ Cache hit (13m 29s remaining)
Time 5:00  → get_access_token() → ✅ Cache hit (8m 30s remaining)
Time 10:00 → get_access_token() → ✅ Cache hit (3m 30s remaining)
Time 13:30 → get_access_token() → ❌ Cache expired (90s safety margin)
              Fetches new token from Cognito
Time 15:00 → Old token actually expires (but we stopped using it at 13:30)
```

### The Buffer Formula

```python
# From src/agent/auth/cognito.py
expires_in = token_data.get("expires_in", 900)  # e.g., 900s (15 min)

# Calculate buffer: 10% of token lifetime, clamped between 60s-300s
buffer_seconds = max(
    buffer_min_seconds,           # Don't go below 60s
    min(
        buffer_max_seconds,       # Don't go above 300s
        expires_in * buffer_percent / 100.0  # 10% of token lifetime
    )
)

# Cache until: now + expires_in - buffer
expiry_time = time.time() + expires_in - buffer_seconds
```

## Configuration Parameters

The buffer behaviour is controlled by three parameters in `config/{env}.yaml`:

```yaml
cognito:
  access_token_validity_minutes: 15   # Cognito token expiry (5-1440 minutes)
  oauth_cache:
    buffer_percent: 10.0              # Cache buffer as % of token lifetime (0.0-50.0)
    buffer_min_seconds: 60            # Minimum cache buffer (seconds)
    buffer_max_seconds: 300           # Maximum cache buffer (seconds, 5 minutes)
```

### 1. `buffer_percent` (Default: 10.0)

**Meaning**: Use a percentage of the token's lifetime as the safety buffer.

**Why?** Tokens of different lifetimes need proportionally sized buffers. A 15-minute token needs less buffer than a 60-minute token.

**Examples:**
- 15-min token (900s) → 10% = **90s buffer**
- 30-min token (1800s) → 10% = **180s buffer**
- 60-min token (3600s) → 10% = **360s buffer** (but capped at 300s)

### 2. `buffer_min_seconds` (Default: 60)

**Meaning**: Never use less than this many seconds as buffer, even for very short tokens.

**Why?** Short-lived tokens need a minimum safety margin to prevent edge cases where the token expires during a request.

**Example:**
- 5-min token (300s) → 10% = 30s → **bumped to 60s** (20% buffer)

### 3. `buffer_max_seconds` (Default: 300)

**Meaning**: Never use more than this many seconds as buffer, even for very long tokens.

**Why?** Long-lived tokens don't need huge buffers. Capping at 5 minutes prevents wasting usable token time while still providing ample safety margin.

**Example:**
- 60-min token (3600s) → 10% = 360s → **capped at 300s** (8.3% buffer)

## Buffer Calculation Examples

| Token Config | Cognito Returns | 10% Calc | After Clamp | Usable Cache | Buffer % |
|--------------|-----------------|----------|-------------|--------------|----------|
| **5 min**    | 300s            | 30s      | **60s** ⬆️  | 240s (4 min) | 20.0%    |
| **15 min**   | 900s            | 90s      | **90s** ✅  | 810s (13.5 min) | 10.0%    |
| **30 min**   | 1800s           | 180s     | **180s** ✅ | 1620s (27 min) | 10.0%    |
| **60 min**   | 3600s           | 360s     | **300s** ⬇️ | 3300s (55 min) | 8.3%     |

**Legend:**
- ⬆️ = Bumped to minimum
- ✅ = Within range (10% applied)
- ⬇️ = Capped at maximum

## Why This Matters

### AgentCore Runtime Container Lifecycle

AgentCore Runtime uses **Firecracker microVMs** with a **session-based lifecycle**:

- **Same session** (`runtimeSessionId`): Container persists and reuses for up to 15 minutes idle (configurable)
- **Module-level cache**: The `_token_cache` variable persists across invocations within the same session
- **Warm starts**: Subsequent invocations reuse the cached token (microseconds vs 100-200ms)

### Performance Impact

**Without caching** (every invocation fetches token):
```
Turn 1: 200ms (Cognito API call)
Turn 2: 200ms (Cognito API call)
Turn 3: 200ms (Cognito API call)
...
Total: 200ms × N invocations
```

**With caching** (first invocation fetches, rest use cache):
```
Turn 1: 200ms (Cognito API call)
Turn 2: 0.1ms (cache hit) ← 99.95% faster!
Turn 3: 0.1ms (cache hit) ← 99.95% faster!
...
Total: 200ms + (0.1ms × N-1)
```

**Over a 10-turn conversation**: 1 Cognito call instead of 10 = **90% reduction**

## Design Rationale

### Why the Buffer?

**Problem**: If we cache until the exact expiry time, requests near expiry might fail mid-flight.

**Solution**: Stop using the cached token before it expires (the "buffer period").

**Analogy**: Like food expiration dates:
- Token expires at "15:00" (best before date)
- Buffer = "throw it out at 13:30" (safety margin)
- 10% buffer = "discard when 10% of shelf life remains"
- Min 60s = "always keep at least 1 minute margin"
- Max 300s = "never waste more than 5 minutes of freshness"

### Why Adaptive Buffering?

Different token lifetimes need different buffer strategies:

- **Short tokens (5-15 min)**: Need larger proportional buffers due to tighter timing windows
- **Medium tokens (30 min)**: 10% buffer is perfect
- **Long tokens (60+ min)**: Don't need huge buffers; cap at 5 minutes for efficiency

The three-parameter system ensures safe, efficient caching across all token lifetime configurations.

## Environment Variables

The configuration is automatically passed to the agent runtime as environment variables:

```bash
OAUTH_CACHE_BUFFER_PERCENT=10.0    # Buffer percentage
OAUTH_CACHE_BUFFER_MIN_SEC=60      # Minimum buffer (seconds)
OAUTH_CACHE_BUFFER_MAX_SEC=300     # Maximum buffer (seconds)
```

These are read at runtime from `src/agent/auth/cognito.py`:

```python
_BUFFER_PERCENT = float(os.getenv("OAUTH_CACHE_BUFFER_PERCENT", "10.0"))
_BUFFER_MIN_SEC = int(os.getenv("OAUTH_CACHE_BUFFER_MIN_SEC", "60"))
_BUFFER_MAX_SEC = int(os.getenv("OAUTH_CACHE_BUFFER_MAX_SEC", "300"))
```

## Tuning Recommendations

### Development Environment
```yaml
cognito:
  access_token_validity_minutes: 15   # Shorter tokens for faster iteration
  oauth_cache:
    buffer_percent: 10.0              # Standard buffer
    buffer_min_seconds: 60
    buffer_max_seconds: 300
```

### Production Environment
```yaml
cognito:
  access_token_validity_minutes: 30   # Longer tokens for better caching
  oauth_cache:
    buffer_percent: 10.0              # Standard buffer
    buffer_min_seconds: 90            # Slightly larger minimum for safety
    buffer_max_seconds: 300
```

### High-Security Environment
```yaml
cognito:
  access_token_validity_minutes: 5    # Very short-lived tokens
  oauth_cache:
    buffer_percent: 15.0              # Larger buffer percentage
    buffer_min_seconds: 60
    buffer_max_seconds: 120           # Lower cap for tighter control
```

## Monitoring

Token cache behaviour is logged at `INFO` or `DEBUG` level:

```
[Auth] Requesting fresh OAuth2 token: endpoint=https://...
[Auth] OAuth2 token obtained and cached: length=1234 client_id=abc expires_in=900s
[Auth] Using cached OAuth2 token: client_id=abc ttl=742s
[Auth] Using cached OAuth2 token: client_id=abc ttl=301s
[Auth] Requesting fresh OAuth2 token: endpoint=https://... (cache expired)
```

Set `agent_runtime.log_level: DEBUG` in your environment config to see cache hits/misses.

### Expected Logging Behavior

**Important**: You may **not** see token logs on every conversational turn. This is normal and indicates efficient connection reuse:

- **First invocation** (e.g., 4:02): MCP client creates connection → token fetched → logged
- **Subsequent invocations** (e.g., 4:05): MCP client reuses existing connection → **no token logs**

Token logs only appear when:
- Container cold starts (new session)
- MCP connection re-establishes (network issue, timeout, error recovery)
- Connection lifetime expires and reconnects

**No token logs ≠ broken caching**. It means the persistent connection is working efficiently.
