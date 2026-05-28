# Release And Registry

## Status

Draft.

## Package Targets

The official server should support:

- Python package for local STDIO use.
- Docker image for remote or managed deployments.
- Versioned source release.

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
