# Agilix Buzz MCP Specs

These specs define the path from the current submission-report proof of concept
to an official-quality Agilix Buzz MCP server.

Read in order:

1. `000-product-scope.md`
2. `001-auth-and-security.md`
3. `002-buzz-domain-model.md`
4. `003-tool-catalog.md`
5. `004-resource-uris.md`
6. `005-error-model.md`
7. `006-test-plan.md`
8. `007-release-and-registry.md`
9. `008-buzz-api-ontology.md`

The implemented PoC covers the read-only submission review slice:

- `buzz.get_activity`
- `buzz.list_activities`
- `buzz.get_submission_report`
- `buzz.get_attachment_url`
- `buzz.docs.search`
- `buzz.docs.get_command`
- `buzz.docs.get_schema`
- `buzz://course/{entityid}/manifest`
- `buzz://course/{entityid}/item/{itemid}`
- `buzz://submission/{enrollmentid}/{itemid}/report{?entityid}`
- `buzz.summarize_submission`
- `buzz.draft_student_feedback`
- `buzz.troubleshoot_submission_access`
