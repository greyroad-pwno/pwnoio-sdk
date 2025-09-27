# Pwno.io SDK

Synchronous Python SDK for submitting a binary (and optional libc), provisioning an analysis machine, and retrieving the MCP link (URL).

## Installation


```bash
git clone https://github.com/greyroad-pwno/pwnoio-sdk.git
cd pwnoio-sdk
pip install -e .
```

## Quick Start

```python
from pwnoio_sdk import PwnoMCPClient

# Initialize client
client = PwnoMCPClient(api_key="sk-pwno-your-api-key")

# Builder pattern - set files first, then analyze
client.set_binary("path/to/binary")
client.set_libc("path/to/libc.so.6")  # optional
result = client.analyze()

# Or you can also analyze directly
result = client.analyze(binary="path/to/binary", libc="path/to/libc.so.6")

print(f"MCP URL: {result.mcp_url}")
print(f"Binaro ID: {result.binaro_id}")
```

### Context Manager

```python
with PwnoMCPClient(api_key="sk-pwno-your-api-key") as client:
    result = client.analyze(binary="path/to/binary")
    print(f"MCP URL: {result.mcp_url}")
```

## Main Objects

- `PwnoMCPClient` (sync): upload/analyze, list binaros, and query machine status.
- `AnalyzeResponse` (dataclass): `mcp_url`, `expires_at`, `status`, `binaro_id`, `task_id`, `message`, `fileinfo`.
- Exceptions: `PwnoError`, `PwnoAPIError`, `PwnoTimeoutError`.

## API Reference

### AnalyzeResponse

Response object from the `analyze()` method:

```python
@dataclass
class AnalyzeResponse:
    mcp_url: str           # URL for MCP connection
    expires_at: str        # When the connection expires
    status: str            # Analysis status
    binaro_id: str         # Unique binary identifier
    task_id: str           # Analysis task identifier
    message: str           # Status message
    fileinfo: Optional[Dict[str, Any]]  # Binary metadata
```

### Exceptions

Custom exceptions for better error handling:

- `PwnoError` - Base exception for all SDK errors
- `PwnoAPIError` - API returned an error response
- `PwnoTimeoutError` - Request timed out
- `PwnoValidationError` - Input validation failed
- `PwnoFileNotFoundError` - Required files not found

## Configuration

### Environment Variables

- `PWNO_API_KEY` - Your API key (format: `sk-pwno-...`)
- `PWNO_BASE_URL` - API base URL (default: `https://backend.pwno.io`)

### Client Options

```python
client = PwnoMCPClient(
    api_key="sk-pwno-your-key",
    base_url="https://backend.pwno.io",  # Custom API endpoint
    timeout=300  # Request timeout in seconds
)
```

## Examples

See the `examples/` directory:
- `quickstart_analyze.py` – submit binary/libc and print MCP URL
- `check_status.py` – read machine status by `binaro_id`

## Error Handling

```python
from pwnoio_sdk import PwnoMCPClient, PwnoError, PwnoAPIError

try:
    client = PwnoMCPClient(api_key="sk-pwno-your-key")
    result = client.analyze(binary="nonexistent.bin")
except PwnoFileNotFoundError as e:
    print(f"File not found: {e}")
except PwnoAPIError as e:
    print(f"API error {e.status_code}: {e}")
except PwnoError as e:
    print(f"SDK error: {e}")
```

## API Compatibility

Supported endpoints (v1):
- `/v1/analyze` (multipart: `binary` + optional `libc`) → returns `mcp_url`
- `/v1/health`
- `/v1/binaro/`, `/v1/binaro/{binaro_id}`
- `/v1/binaro/{binaro_id}/machine`, `/v1/binaro/{binaro_id}/machine/status`

[!] Interacting with the MCP instance itself (e.g., via WebSocket) is outside of this SDK’s scope

## Development

```bash
pip install -e .
```

## API Docs

- API Reference: https://backend.pwno.io/scalar/
