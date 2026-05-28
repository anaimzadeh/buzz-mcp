# Tool Catalog

## Status

Draft.

## Naming

Tool names use the `buzz.` prefix in specification text. Implementations may
also expose backwards-compatible unprefixed aliases when client libraries do not
support dotted names cleanly.

## PoC Tools

### `buzz.get_activity`

Fetch normalized metadata for a single course activity.

Inputs:

- `entityid` string, required.
- `itemid` string, required.

Output:

- `ActivityItem`.

### `buzz.list_activities`

Fetch normalized metadata for every visible activity item in a course.

Inputs:

- `entityid` string, required.

Output:

- `entityid`
- `count`
- `activities` array of `ActivityItem`.

### `buzz.get_submission_report`

Fetch and normalize a complete human-readable submission report.

Inputs:

- `enrollmentid` string, required unless provided through `submissionid`.
- `itemid` string, required unless provided through `submissionid`.
- `entityid` string, required unless provided through `submissionid`.
- `submissionid` string, optional JSON or colon-separated convenience value.

Output:

- `Submission`.

### `buzz.get_attachment_url`

Build an authenticated URL for a known submission or attempt attachment.

Inputs:

- `enrollmentid` string, required.
- `itemid` string, required.
- `filepath` string, required.
- `source` enum: `submission` or `attempt-question`.
- `partid` string, required when `source` is `attempt-question`.

Output:

- `download_url`
- `expires_at` when known, otherwise omitted.

## Next Read-Only Tools

- `buzz.get_course`
- `buzz.list_courses`
- `buzz.get_user`
- `buzz.list_enrollments`
- `buzz.get_gradebook`
- `buzz.get_submission_state`
- `buzz.search_course_content`

## Future Write Tools

Write tools are out of PoC scope:

- `buzz.put_teacher_response`
- `buzz.update_grade`
- `buzz.send_message`
- `buzz.update_activity_metadata`

Every write tool must have a dedicated safety spec before implementation.
