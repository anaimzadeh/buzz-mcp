# Error Model

## Status

Draft.

## Error Codes

### `AUTH_REQUIRED`

Buzz credentials or MCP authorization are missing or expired.

### `INSUFFICIENT_BUZZ_RIGHTS`

Buzz rejected the operation because the authenticated user lacks rights.

### `NOT_FOUND`

The requested Buzz entity does not exist or is not visible to the caller.

### `RATE_LIMITED`

Buzz or the MCP server rate limit was exceeded.

### `BUZZ_API_ERROR`

Buzz returned an HTTP or DLAP error that does not map to a narrower code.

### `INVALID_ID`

The input ID is missing, malformed, or cannot be decoded into required Buzz IDs.

### `UNSUPPORTED_ACTIVITY_TYPE`

The activity exists, but the requested report cannot be generated for its type.

### `REDACTED_FOR_PRIVACY`

The server intentionally omitted data due to privacy policy.

## Error Shape

Tool execution errors should include:

- `code`
- `message`
- `retryable`
- `details` with safe, non-secret context

## Redaction

Errors must redact:

- Passwords.
- `_token` query parameters.
- Session cookies.
- Full authenticated attachment URLs.
