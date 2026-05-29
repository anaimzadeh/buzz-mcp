# Test Plan

## Status

Partially implemented for local and CI unit, contract, package, Docker, MCP
Inspector smoke, and manual live sandbox release-gate checks.

## Unit Tests

- Normalize submission request inputs.
- Parse item metadata from `GetItem` and `GetItemList`.
- Parse question, choice, order, match, essay, and fileupload answers.
- Extract top-level submission attachments.
- Build authenticated URLs through a fake URL builder.
- Redact tokens in error paths.
- Search and resolve the local Buzz docs catalog without credentials.

## MCP Contract Tests

- Every tool has stable input validation.
- Every tool returns the documented shape.
- Resource URI parsing rejects malformed URIs.
- Prompt templates include required arguments and safe instructions.

## MCP Inspector Smoke Test

CI runs the pinned official MCP Inspector CLI against the local STDIO server:

```bash
python scripts/mcp_inspector_smoke.py
```

The smoke test verifies that Inspector can initialize the server and list the
expected tools, resource templates, and prompts without live Buzz credentials.

## Integration Tests

Live Buzz tests are opt-in and require:

- `BUZZ_USERNAME`
- `BUZZ_PASSWORD`
- `BUZZ_DOMAIN`
- `BUZZ_TEST_ENTITYID`
- `BUZZ_TEST_ITEMID`
- `BUZZ_TEST_ENROLLMENTID`

Integration tests must be skipped by default.

Run them explicitly with:

```bash
export BUZZ_RUN_LIVE_TESTS=1
export BUZZ_USERNAME="teacher"
export BUZZ_PASSWORD="secret"
export BUZZ_DOMAIN="myschool"
export BUZZ_TEST_ENTITYID="4378"
export BUZZ_TEST_ITEMID="assign12"
export BUZZ_TEST_ENROLLMENTID="4317"
PYTHONPATH=src python -m unittest tests.test_live_buzz
```

`BUZZ_TEST_ATTACHMENT_FILEPATH` is optional and enables direct attachment URL
contract coverage.

For release validation, the `Live Buzz Sandbox` GitHub Actions workflow runs the
same live tests manually against the protected `buzz-sandbox` environment. The
workflow requires the same Buzz secrets and `BUZZ_TEST_SANDBOX_ACK=1`, which
confirms that the target tenant and submission are safe for live validation.

## Security Tests

- No secrets in exception strings.
- No secrets in logs.
- Missing credentials return `AUTH_REQUIRED`.
- Permission failures map to `INSUFFICIENT_BUZZ_RIGHTS` when Buzz exposes enough signal.

## Release Gate

A release candidate requires:

- All unit tests passing in CI.
- Python package build passing in CI.
- Docker image build passing in CI.
- MCP Inspector smoke test passing in CI.
- Manual `Live Buzz Sandbox` workflow passing in a non-production Buzz tenant.
- Changelog entry.
- Security review of any new write operation.
