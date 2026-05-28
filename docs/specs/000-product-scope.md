# Product Scope

## Status

Draft for the read-only proof of concept.

## Goal

Create an official-quality MCP server for Agilix Buzz that exposes safe,
task-oriented access to Buzz data for AI clients without leaking credentials,
student data, or raw DLAP implementation details.

## Users

- Teachers reviewing submissions, gradebook state, and student progress.
- School support staff troubleshooting courses, enrollments, activities, and submissions.
- Administrators auditing Buzz structure and access issues.
- AI clients that need stable, documented tools and context resources.

## Non-Goals

- Mirror every Buzz/DLAP command as a generic tool.
- Add write operations before read-only contracts and permission behavior are stable.
- Bypass Buzz permissions or tenant isolation.
- Store long-lived student data outside Buzz.

## Proof-of-Concept Scope

The PoC is read-only and centered on submission review:

- Resolve an activity item by `entityid` and `itemid`.
- Fetch a student submission by `enrollmentid` and `itemid`.
- Resolve question and choice identifiers into human-readable Q&A.
- Return authenticated attachment links only when the caller is authorized by Buzz.
- Expose the same report as a task-oriented tool and a stable MCP resource URI.
- Provide prompt templates for common teacher/support workflows.

## Official Acceptance Criteria

- Tools have stable names, typed inputs, and documented output contracts.
- Resource URIs are stable and do not expose secrets.
- Authentication and logging rules are documented and tested.
- All read-only tools pass fixture tests and live sandbox tests.
- Write tools are absent or gated behind explicit policy controls.
- Release metadata is ready for package registries and the MCP Registry.
