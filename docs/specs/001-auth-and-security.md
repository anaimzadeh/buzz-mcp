# Auth And Security

## Status

Draft.

## Modes

### Local STDIO

Local STDIO servers read Buzz credentials from environment variables:

- `BUZZ_USERNAME`
- `BUZZ_PASSWORD`
- `BUZZ_DOMAIN`
- `BUZZ_BASE_URL` optional, defaulting to `https://api.agilixbuzz.com`

This mode is suitable for local clients and development.

### Remote HTTP

Remote deployments must use MCP HTTP authorization and act as a protected
resource server. The preferred production design is per-user delegation to Buzz.
If Buzz tenant configuration cannot support OAuth-style delegation, a secure
credential broker must map the MCP user to tenant-approved Buzz credentials.

## Credential Rules

- Never log passwords, DLAP tokens, or full authenticated URLs.
- Never persist Buzz credentials in project files.
- Redact `_token`, `password`, and equivalent secrets in exceptions and telemetry.
- Prefer short-lived tokens and refresh through Buzz-supported mechanisms.

## Access Control

Each MCP tool must:

- Authenticate before calling Buzz.
- Let Buzz enforce tenant and role permissions.
- Convert Buzz permission failures to `INSUFFICIENT_BUZZ_RIGHTS`.
- Avoid cross-tenant fallback behavior.

## Data Privacy

- Treat student submissions, grades, teacher responses, and attachments as student data.
- Return only the fields required by the requested workflow.
- Avoid hidden expansion of large resources.
- Provide clear tool descriptions so clients can show meaningful consent prompts.

## Write Safety

The official server starts read-only. Future write tools must:

- Use separate enablement flags.
- Require narrowly typed inputs.
- Return a preview or dry-run result when possible.
- Be named with explicit verbs such as `put_teacher_response` or `update_grade`.
- Be covered by audit logging.
