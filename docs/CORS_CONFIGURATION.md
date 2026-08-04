# CORS Configuration Guide

## Overview

Cross-Origin Resource Sharing (CORS) is a security feature that restricts which domains can access the CodeMind API. Proper CORS configuration is critical to prevent CSRF attacks and unauthorized access from malicious websites.

## Security Context

**Why CORS Matters:**
- Without CORS restrictions, any website can make requests to your API
- Attackers could trick users into making unauthorized API calls from malicious sites
- Proper CORS configuration is a defense-in-depth security measure

**What We Fixed:**
- ❌ **Before**: `allow_origins=["*"]` - Wide open to any origin!
- ✅ **After**: Specific allowed origins from environment configuration

## Configuration

### Environment Variable

CORS origins are configured via the `ALLOWED_ORIGINS` environment variable in your `.env` file.

**Format:**
```bash
ALLOWED_ORIGINS=origin1,origin2,origin3
```

**Important:**
- Comma-separated list (no spaces between origins)
- Each origin must include the protocol (`http://` or `https://`)
- Each origin must include the port if not standard (80/443)

### Development Setup

For local development, your `.env` file:

```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

This allows:
- Frontend dev server (typically on port 3000)
- API dev server (typically on port 8000)

### Production Setup

For production, your `.env` file:

```bash
# CORS Configuration
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

**Production Best Practices:**
- ✅ Use HTTPS origins only
- ✅ List only the specific domains that need access
- ✅ Don't include development origins in production
- ✅ Use separate `.env` files for each environment

## Examples

### Single Origin

```bash
ALLOWED_ORIGINS=https://app.mycompany.com
```

### Multiple Origins

```bash
ALLOWED_ORIGINS=https://app.mycompany.com,https://admin.mycompany.com,https://dashboard.mycompany.com
```

### Development + Staging

```bash
# Development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Staging
ALLOWED_ORIGINS=https://staging-app.mycompany.com,https://staging-admin.mycompany.com

# Production
ALLOWED_ORIGINS=https://app.mycompany.com,https://admin.mycompany.com
```

## CORS Headers Configured

The API sets the following CORS headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `Access-Control-Allow-Origin` | From `ALLOWED_ORIGINS` | Allowed origins |
| `Access-Control-Allow-Credentials` | `true` | Allow cookies/auth headers |
| `Access-Control-Allow-Methods` | `GET, POST, PUT, DELETE` | Allowed HTTP methods |
| `Access-Control-Allow-Headers` | `*` | Allowed request headers |

## Testing CORS

### Manual Testing with curl

Test if an origin is allowed:

```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/analyze/upload -v
```

Look for these headers in the response:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE
```

### Automated Tests

Run the CORS test suite:

```bash
pytest tests/integration/test_api_authentication.py::TestAPIAuthentication::test_cors_allowed_origin -v
pytest tests/integration/test_api_authentication.py::TestAPIAuthentication::test_cors_disallowed_origin -v
pytest tests/integration/test_api_authentication.py::TestAPIAuthentication::test_cors_preflight_request -v
```

## Common Issues

### Issue: CORS error in browser

**Error:**
```
Access to fetch at 'https://api.example.com/analyze' from origin 'https://app.example.com' 
has been blocked by CORS policy
```

**Solution:**
1. Check your `.env` file has the correct origin:
   ```bash
   ALLOWED_ORIGINS=https://app.example.com
   ```
2. Make sure to include the protocol (`https://`)
3. Restart the API server after changing `.env`

### Issue: Multiple origins not working

**Wrong:**
```bash
ALLOWED_ORIGINS=https://app.com, https://admin.com  # Has spaces!
```

**Correct:**
```bash
ALLOWED_ORIGINS=https://app.com,https://admin.com  # No spaces
```

### Issue: Localhost with port not working

**Wrong:**
```bash
ALLOWED_ORIGINS=localhost:3000  # Missing protocol
```

**Correct:**
```bash
ALLOWED_ORIGINS=http://localhost:3000  # Include http://
```

## Security Warnings

### ⚠️ Never Use Wildcard in Production

**NEVER do this:**
```python
allow_origins=["*"]  # Extremely insecure!
```

This allows any website to make requests to your API, making you vulnerable to:
- CSRF attacks
- Data theft
- Unauthorized API usage
- Credential leakage

### ⚠️ Don't Allow All Subdomains

**Be specific:**
```bash
# Bad - too permissive
ALLOWED_ORIGINS=https://*.mycompany.com

# Good - explicit
ALLOWED_ORIGINS=https://app.mycompany.com,https://admin.mycompany.com
```

Note: The current implementation doesn't support wildcard subdomains. This is intentional for security.

### ⚠️ Use HTTPS in Production

**Development:**
```bash
ALLOWED_ORIGINS=http://localhost:3000  # OK for development
```

**Production:**
```bash
ALLOWED_ORIGINS=https://app.example.com  # Always use HTTPS
```

## Troubleshooting

### Check Current Configuration

Add logging to see what origins are loaded:

```python
# In codemind_api.py, after loading allowed_origins
print(f"Allowed CORS origins: {allowed_origins}")
```

### Verify Environment Variable

```bash
# Check what's in your .env
grep ALLOWED_ORIGINS .env

# Check what the app sees
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('ALLOWED_ORIGINS'))
"
```

### Test with Browser DevTools

1. Open your frontend in the browser
2. Open DevTools (F12) → Console
3. Make an API request
4. Check the Network tab for CORS headers
5. Look for `access-control-allow-origin` in the response headers

## Multiple Environments

Use environment-specific `.env` files:

```
.env.development
.env.staging
.env.production
```

Load the appropriate one based on your deployment:

```bash
# Development
cp .env.development .env

# Staging
cp .env.staging .env

# Production
cp .env.production .env
```

Or use environment variable overrides in your deployment pipeline:

```bash
# Docker
docker run -e ALLOWED_ORIGINS=https://app.example.com myapp

# Kubernetes
env:
  - name: ALLOWED_ORIGINS
    value: "https://app.example.com"
```

## Related Documentation

- [API Authentication](./API_AUTHENTICATION.md)
- [Mozilla CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

## Support

For CORS-related issues:
1. Check this documentation
2. Verify your `.env` configuration
3. Run the CORS test suite
4. Check browser DevTools for CORS error messages
