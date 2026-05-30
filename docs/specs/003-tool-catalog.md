# Tool Catalog

## Status

Partially implemented for the read-only submission review tools and local Buzz
docs metadata tools. The first core entity graph slice is also implemented for
courses and enrollments.

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

### `buzz.get_item`

Fetch richer normalized metadata for a single course content item. This returns
stable navigation, resource, grading, and dropbox fields without returning raw
free-form item data or item content payloads.

Inputs:

- `entityid` string, required.
- `itemid` string, required.
- `version` string, optional.

Output:

- `Item`.

### `buzz.list_items`

Fetch a bounded list of normalized course content items. The first
implementation does not expose Buzz's free-form `query`, `itemid`, or
`allversions` parameters.

Inputs:

- `entityid` string, required.
- `limit` integer, optional; default `100`, max `100`.

Output:

- `entityid`
- `count`
- `total_count`
- `limit`
- `truncated`
- `items` array of `Item`.

### `buzz.list_activities`

Fetch normalized metadata for every visible activity item in a course.

Inputs:

- `entityid` string, required.

Output:

- `entityid`
- `count`
- `activities` array of `ActivityItem`.

### `buzz.get_manifest`

Fetch a bounded, depth-first summary of a Buzz course content manifest. This is
the first richer content-graph tool; it returns item hierarchy/navigation
metadata without raw course data or item content payloads.

Inputs:

- `entityid` string, required.
- `limit` integer, optional; default `100`, max `500`.

Output:

- `Manifest`.

### `buzz.get_submission_report`

Fetch and normalize a complete human-readable submission report.

Inputs:

- `enrollmentid` string, required unless provided through `submissionid`.
- `itemid` string, required unless provided through `submissionid`.
- `entityid` string, required unless provided through `submissionid`.
- `submissionid` string, optional JSON or colon-separated convenience value.

Output:

- `Submission`.

### `buzz.get_course`

Fetch normalized metadata for a Buzz course or course-like entity.

Inputs:

- `courseid` string, required.
- `version` string, optional.

Output:

- `Course`.

### `buzz.list_courses`

Fetch normalized course records for an explicit Buzz domain. This tool does not
allow `domainid=0`, raw free-form `query`, deleted/all course scope, or optional
`select` expansions in this first implementation.

Inputs:

- `domainid` string, required and must not be `0`.
- `includedescendantdomains` boolean, optional; default `false`.
- `show` enum: `current` or `active`; default `current`.
- `text` string, optional; matches course ID, reference, or title per Buzz.
- `limit` integer, optional; default `50`, max `100`.

Output:

- `domainid`
- `includedescendantdomains`
- `show`
- `text` when provided.
- `count`
- `limit`
- `courses` array of `Course`.

### `buzz.get_enrollment`

Fetch one normalized Buzz enrollment record.

Inputs:

- `enrollmentid` string, required.

Output:

- `Enrollment`.

### `buzz.get_user`

Fetch privacy-redacted metadata for a Buzz user. The tool uses the default
`GetUser2` response and does not request optional `data`, `securityconfig`,
`session`, or `history` expansions.

Inputs:

- `userid` string, required.

Output:

- `User`.

### `buzz.list_user_enrollments`

Fetch normalized enrollment records for a Buzz user.

Inputs:

- `userid` string, required.
- `entityid` string, optional.
- `allstatus` boolean, optional; default `false`.
- `limit` integer, optional; default `50`, max `100`.

Output:

- `userid`
- `entityid` when provided.
- `count`
- `limit`
- `enrollments` array of `Enrollment`.

### `buzz.list_entity_enrollments`

Fetch normalized enrollment records for a Buzz course/entity.

Inputs:

- `entityid` string, required.
- `userid` string, optional.
- `allstatus` boolean, optional; default `false`.
- `limit` integer, optional; default `50`, max `100`.

Output:

- `entityid`
- `userid` when provided.
- `count`
- `limit`
- `enrollments` array of `Enrollment`.

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

### `buzz.docs.search`

Search the local high-value Buzz documentation catalog for command, schema,
enum, and concept metadata. This is a static, credential-free implementation
aid; it does not scrape Buzz docs at runtime.

Inputs:

- `query` string, optional.
- `entry_type` enum: `any`, `command`, `schema`, `enum`, or `concept`.
- `limit` integer, 1 through 50.

Output:

- `query`
- `count`
- `results` array of documentation entries.

### `buzz.docs.get_command`

Return local metadata for a known high-value Buzz DLAP command.

Inputs:

- `name` string, required.

Output:

- Documentation entry.

### `buzz.docs.get_schema`

Return local metadata for a known high-value Buzz schema.

Inputs:

- `name` string, required.

Output:

- Documentation entry.

## Next Read-Only Tools

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
