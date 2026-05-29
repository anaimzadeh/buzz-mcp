# Release And Registry

## Status

Partially implemented for local STDIO package metadata, source-built Docker
runtime, and CI release-gate checks including MCP Inspector smoke coverage.

## Package Targets

The official server should support:

- Python package for local STDIO use.
- Docker image for remote or managed deployments.
- Versioned source release.

The PoC Dockerfile builds from local source and starts the STDIO server with
`agilix-buzz-mcp`.

The source distribution manifest includes registry metadata, spec documents,
and the MCP Inspector smoke-test script used by the release gate.

## Versioning

Use semantic versioning:

- Patch: bug fixes with no contract changes.
- Minor: additive tools, resources, prompts, or output fields.
- Major: breaking input/output, auth, or deployment changes.

## Registry Metadata

Prepare MCP Registry metadata with:

- Verified namespace controlled by Agilix, preferably `com.agilix/buzz`.
- Public repository or public remote endpoint.
- Installation instructions.
- Auth requirements.
- Support and security contact.

The PoC currently uses a provisional GitHub namespace in `server.json`:

```text
io.github.anaimzadeh/agilix-buzz-mcp
```

This must be replaced with an Agilix-controlled namespace before any official
release.

## Documentation

Each release must document:

- Tool catalog.
- Resource URI templates.
- Prompt catalog.
- Required Buzz credentials and rights.
- Privacy behavior.
- Known unsupported Buzz activity types.

## Official Branding Requirements

Do not call the server official until Agilix approves:

- Repository ownership or transfer.
- Naming and logos.
- Support channel.
- Security disclosure process.
- Release process.
