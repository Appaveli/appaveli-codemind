# Upload Security

## Overview

Comprehensive security validation for file uploads in the CodeMind API, implementing defense-in-depth protections against common upload vulnerabilities.

## Security Features Implemented

### 1. File Size Limits
- **Default limit**: 10 MB per file
- **ZIP files**: 50 MB (for project uploads)
- **Configurable**: Via `MAX_UPLOAD_SIZE` and `MAX_ZIP_SIZE` environment variables
- **Protection**: Prevents DoS attacks via large file uploads

### 2. Extension Validation
- **Allowlist approach**: Only explicitly allowed file extensions are accepted
- **Supported code files**: `.py`, `.java`, `.js`, `.ts`, `.tsx`, `.jsx`, `.swift`, `.kt`, `.php`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.rb`, and more
- **Project uploads**: `.zip` files for security scanning
- **Protection**: Blocks executable files (.exe, .dll, .so) and other dangerous types

### 3. MIME Type Validation
- **Content-Type checking**: Validates MIME types against an allowlist
- **Prevents**: MIME type spoofing attacks
- **Supported types**: text/plain, text/x-python, application/javascript, application/zip, etc.

### 4. Filename Sanitization
- **Path traversal protection**: Blocks `../` sequences
- **Character filtering**: Removes/rejects dangerous characters (`<>:"|?*`, backslashes)
- **Path normalization**: Extracts basename only, prevents absolute paths
- **Protection**: Prevents writing files outside intended directories

### 5. Rate Limiting
- **Per-IP limiting**: 10 uploads per 60-second window (default)
- **Sliding window**: Old requests automatically expire
- **Proxy-aware**: Respects X-Forwarded-For header
- **Protection**: Prevents upload flooding and abuse

### 6. Upload Logging
- **Comprehensive logging**: All uploads logged with filename, size, IP, MIME type
- **Security events**: Failed validation attempts logged at WARNING level
- **Audit trail**: Full tracking for security investigations

## Configuration

### Environment Variables

```bash
# Maximum file size (bytes) - default 10MB
MAX_UPLOAD_SIZE=10485760

# Maximum ZIP file size (bytes) - default 50MB
MAX_ZIP_SIZE=52428800

# Rate limiting (set in code, future: env vars)
UPLOAD_RATE_LIMIT_PER_IP=10
UPLOAD_RATE_WINDOW_SECONDS=60
```

## Error Responses

### File Too Large (413)
```json
{
  "detail": "File too large: 11534336 bytes exceeds limit of 10485760 bytes (10MB)"
}
```

### Invalid Extension (400)
```json
{
  "detail": "Unsupported file type: .exe. Allowed: .c, .cpp, .cs, .go, .java, ..."
}
```

### Path Traversal (400)
```json
{
  "detail": "Invalid filename: contains forbidden characters or patterns"
}
```

### Rate Limit Exceeded (429)
```json
{
  "detail": "Rate limit exceeded: maximum 10 uploads per 60 seconds. Please try again later."
}
```
Headers include: `Retry-After: 60`

## Architecture

### Modules

1. **`upload_validation.py`**
   - File size validation
   - Extension validation
   - MIME type validation
   - Filename sanitization
   - Main `validate_upload()` orchestration

2. **`rate_limiter.py`**
   - In-memory rate limiting (per IP)
   - Sliding window implementation
   - X-Forwarded-For support

3. **`codemind_api.py`** (updated)
   - All three upload endpoints secured:
     - `/analyze/upload`
     - `/refactor/upload`
     - `/security/upload`

## Usage Example

### Valid Upload
```python
import requests

files = {
    'file': ('example.py', open('example.py', 'rb'), 'text/x-python')
}
headers = {
    'X-API-Key': 'your_api_key'
}

response = requests.post(
    'http://localhost:8000/analyze/upload',
    files=files,
    headers=headers
)
```

### Handling Errors
```python
if response.status_code == 413:
    print("File too large - reduce size or split project")
elif response.status_code == 400:
    print(f"Validation error: {response.json()['detail']}")
elif response.status_code == 429:
    retry_after = response.headers.get('Retry-After', 60)
    print(f"Rate limited - retry after {retry_after}s")
```

## Security Checklist

✅ File size limits enforced  
✅ Extension allowlist validation  
✅ MIME type validation  
✅ Filename sanitization  
✅ Path traversal protection  
✅ Rate limiting per IP  
✅ Comprehensive logging  
✅ Clear error messages  

## Future Enhancements

### Planned (Not Yet Implemented)

- **Virus Scanning**: ClamAV integration for malware detection
  - Requires ClamAV daemon (`clamd`) setup
  - See `docs/VIRUS_SCANNING_SETUP.md` (future)

- **Content Validation**: Deep inspection beyond MIME type
  - Magic byte validation
  - Polyglot file detection

- **Distributed Rate Limiting**: Redis-based rate limiting
  - Required for multi-instance deployments
  - Shared state across API servers

## Testing

### Run Unit Tests
```bash
pytest tests/unit/test_upload_validation.py -v
pytest tests/unit/test_rate_limiter.py -v
```

### Run Integration Tests
```bash
pytest tests/integration/test_upload_security.py -v
```

### Coverage
```bash
pytest tests/ --cov=appaveli_codemind.web_api.upload_validation --cov=appaveli_codemind.web_api.rate_limiter
```

## Security Considerations

1. **Rate Limiting**: Current implementation is in-memory. For production with multiple API instances, use Redis-based rate limiting.

2. **File Storage**: Temporary files are created during processing. Ensure:
   - Proper cleanup (handled via `finally` blocks)
   - Restricted permissions on temp directories
   - Sufficient disk space monitoring

3. **Logging**: Ensure logs don't contain sensitive data:
   - ✅ Log filenames (sanitized)
   - ✅ Log file sizes
   - ✅ Log IP addresses
   - ❌ Don't log file contents

4. **DoS Protection**: Rate limiting provides basic DoS protection. Consider:
   - Infrastructure-level rate limiting (nginx, CloudFlare)
   - Distributed rate limiting for multi-instance setups
   - Resource monitoring and alerts

## References

- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- CWE-434 (Unrestricted Upload): https://cwe.mitre.org/data/definitions/434.html
- CWE-22 (Path Traversal): https://cwe.mitre.org/data/definitions/22.html
