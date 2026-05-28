# Test Plan

## Status

Draft.

## Unit Tests

- Normalize submission request inputs.
- Parse item metadata from `GetItem` and `GetItemList`.
- Parse question, choice, order, match, essay, and fileupload answers.
- Extract top-level submission attachments.
- Build authenticated URLs through a fake URL builder.
- Redact tokens in error paths.

## MCP Contract Tests

- Every tool has stable input validation.
- Every tool returns the documented shape.
- Resource URI parsing rejects malformed URIs.
- Prompt templates include required arguments and safe instructions.

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

## Security Tests

- No secrets in exception strings.
- No secrets in logs.
- Missing credentials return `AUTH_REQUIRED`.
- Permission failures map to `INSUFFICIENT_BUZZ_RIGHTS` when Buzz exposes enough signal.

## Release Gate

A release candidate requires:

- All unit tests passing.
- MCP Inspector smoke test passing.
- Live sandbox test passing in a non-production Buzz tenant.
- Changelog entry.
- Security review of any new write operation.
