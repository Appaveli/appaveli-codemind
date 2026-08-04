# CodeMind API Authentication

## Overview

The CodeMind Web API uses API key authentication to secure all endpoints. This document describes how to generate, use, and manage API keys.

## Security Features

- **API Key Authentication**: All endpoints (except `/health`) require a valid API key
- **Bcrypt Hashing**: API keys are hashed with bcrypt before storage
- **Rate Limiting**: Each API key has a configurable rate limit (requests per minute)
- **CORS Restrictions**: Only specified origins are allowed
- **Admin-Only Key Management**: Only admins can create and manage API keys

## Quick Start

### 1. Get an API Key

For development, a default API key is available:

```
cm_dev_key_12345678901234567890
```

**⚠️ WARNING**: This key is for development only. Never use it in production!

For production, contact your administrator to generate a dedicated API key.

### 2. Make an API Request

Include your API key in the `X-API-Key` header:

```bash
curl -X POST \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@example.py" \
  https://api.example.com/analyze/upload
```

### 3. Check Rate Limits

The API includes rate limit information in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
```

## API Endpoints

### Public Endpoints (No Authentication Required)

- `GET /health` - Health check endpoint
- `GET /docs` - API documentation
- `GET /openapi.json` - OpenAPI specification

### Protected Endpoints (API Key Required)

- `POST /analyze/upload` - Analyze a code file
- `POST /refactor/upload` - Refactor a code file
- `POST /security/upload` - Security scan of file or project

### Admin Endpoints (Admin Key Required)

- `POST /api-keys/create` - Create a new API key
- `GET /api-keys/list` - List all API keys

## Admin: Creating API Keys

Administrators can create new API keys using the admin endpoints.

### Create a New API Key

```bash
curl -X POST \
  -H "X-Admin-Key: admin_secret_key_change_me" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key - Frontend",
    "rate_limit": 1000
  }' \
  https://api.example.com/api-keys/create
```

Response:

```json
{
  "api_key": "cm_XYZ123...",
  "key_id": "a1b2c3d4",
  "name": "Production Key - Frontend",
  "rate_limit": 1000,
  "message": "API key created successfully. Store it securely - it won't be shown again."
}
```

**⚠️ IMPORTANT**: 
- The API key is only shown once during creation
- Store it securely (e.g., in a password manager or secrets vault)
- Never commit API keys to version control

### List API Keys

```bash
curl -X GET \
  -H "X-Admin-Key: admin_secret_key_change_me" \
  https://api.example.com/api-keys/list
```

Response:

```json
{
  "keys": [
    {
      "key_id": "a1b2c3d4",
      "name": "Production Key - Frontend",
      "created_at": "2026-08-04T10:30:00",
      "rate_limit": 1000,
      "is_active": true,
      "request_count": 42
    }
  ]
}
```

## Error Responses

### 401 Unauthorized

Missing or invalid API key:

```json
{
  "detail": "Missing API key. Include X-API-Key header.",
  "error": "unauthorized"
}
```

```json
{
  "detail": "Invalid API key.",
  "error": "unauthorized"
}
```

### 429 Too Many Requests

Rate limit exceeded:

```json
{
  "detail": "Rate limit exceeded. Limit: 100 requests per minute.",
  "error": "rate_limit_exceeded",
  "rate_limit": 100
}
```

## Rate Limiting

Each API key has a rate limit (requests per minute). The default is 100 requests/minute, but this can be customized when creating a key.

Rate limit information is included in every response:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
```

When you exceed your rate limit:
- You'll receive a `429 Too Many Requests` response
- The limit resets every 60 seconds
- Monitor the `X-RateLimit-Remaining` header to avoid hitting limits

## Best Practices

### Security

1. **Never share API keys** - Each user/application should have its own key
2. **Store keys securely** - Use environment variables or secrets managers
3. **Rotate keys regularly** - Generate new keys and revoke old ones periodically
4. **Use different keys per environment** - Separate keys for dev, staging, production

### Rate Limiting

1. **Monitor rate limits** - Check the `X-RateLimit-Remaining` header
2. **Implement backoff** - Wait before retrying if you hit rate limits
3. **Request limit increases** - Contact admin if you need higher limits

### Error Handling

```python
import requests

response = requests.post(
    "https://api.example.com/analyze/upload",
    headers={"X-API-Key": api_key},
    files={"file": open("example.py", "rb")}
)

if response.status_code == 401:
    print("Authentication failed. Check your API key.")
elif response.status_code == 429:
    print("Rate limit exceeded. Try again in 60 seconds.")
    # Implement exponential backoff here
elif response.status_code == 200:
    print("Success:", response.json())
else:
    print(f"Error {response.status_code}: {response.text}")
```

## Python Example

```python
import requests
import os

# Load API key from environment variable
API_KEY = os.environ.get("CODEMIND_API_KEY")
BASE_URL = "https://api.example.com"

def analyze_file(file_path):
    """Analyze a code file using CodeMind API"""
    
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/analyze/upload",
            headers={"X-API-Key": API_KEY},
            files={"file": f},
            data={"summary_only": "false"}
        )
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise Exception("Invalid API key")
    elif response.status_code == 429:
        raise Exception("Rate limit exceeded")
    else:
        raise Exception(f"API error: {response.status_code}")

# Usage
if __name__ == "__main__":
    result = analyze_file("example.py")
    print(f"Language: {result['language']}")
    print(f"Issues found: {len(result['security_issues'])}")
```

## Configuration

### Admin Key

The admin key is loaded from the `.env` file. To set it up:

1. Copy `.env.example` to `.env` if not already done:
   ```bash
   cp .env.example .env
   ```

2. Generate a secure admin key:
   ```bash
   python -c "import secrets; print(f'cm_admin_{secrets.token_urlsafe(32)}')"
   ```

3. Set the `CODEMIND_ADMIN_KEY` in your `.env` file:
   ```bash
   CODEMIND_ADMIN_KEY=cm_admin_your_generated_key_here
   ```

4. **Important Security Notes:**
   - Never commit `.env` to version control (already in `.gitignore`)
   - Use `.env.example` as a template for new team members
   - Rotate the admin key regularly
   - Use different admin keys for dev/staging/production environments

### CORS Origins

Update the allowed origins in `codemind_api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Development
        "https://app.example.com",    # Production frontend
    ],
    # ...
)
```

## Future Enhancements

When PostgreSQL is added to the project:

- API keys will be stored in the database instead of memory
- Key metadata (usage stats, last used, etc.) will be persisted
- User accounts and key associations will be implemented
- More sophisticated rate limiting (per user, per endpoint, etc.)

## Support

For issues or questions about API authentication:

1. Check the `/docs` endpoint for interactive API documentation
2. Review this documentation
3. Contact your system administrator
