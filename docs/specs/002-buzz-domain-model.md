# Buzz Domain Model

## Status

Partially implemented for `Course`, `Enrollment`, `ActivityItem`, `Item`,
`Submission`, and `Attachment` read contracts.

## Principle

The MCP contract exposes stable Buzz concepts, not raw DLAP XML. DLAP command
shape can change behind the service layer as long as these domain contracts hold.

## Core Entities

### Domain

Represents a Buzz tenant or domain.

Required fields:

- `id`
- `name`

### User

Represents a Buzz user.

Required fields:

- `id`
- `display_name`
- `reference`

Implemented optional fields:

- `domainid`
- `guid`
- `version`
- `pii_redacted`

The normalized user contract intentionally omits email, username, login dates,
password-change dates, free-form data, security configuration, and session data
by default.

### Course

Represents a course or course-like entity.

Required fields:

- `entityid`
- `title`
- `type`

Implemented optional fields:

- `domainid`
- `reference`
- `guid`
- `baseid`
- `start_date`
- `end_date`
- `days`
- `term`
- `version`

### Enrollment

Represents a user's enrollment in a course.

Required fields:

- `enrollmentid`
- `entityid`
- `userid`
- `role`
- `status`

Implemented optional fields:

- `roleid`
- `privileges`
- `domainid`
- `reference`
- `guid`
- `start_date`
- `end_date`
- `first_activity_date`
- `last_activity_date`
- `version`

Until role lookup is implemented, `role` is derived from Buzz's `role`,
`roleid`, or `privileges` attributes in that order.

### ActivityItem

Represents an item in a course manifest.

Required fields:

- `itemid`
- `title`
- `type`
- `abbreviation`
- `accepts_file_upload`
- `allowed_filetypes`
- `dropbox_multiple`
- `perfect_score`
- `due_date`

### Item

Represents a richer normalized course content item read from Buzz item data.

Required fields:

- `entityid`
- `id`
- `title`
- `type`
- `parentid`
- `sequence`
- `abbreviation`
- `href`
- `folder`
- `category`
- `period`
- `resourceentityid`
- `creation_date`
- `modified_date`
- `version`
- `origin_depth`
- `derivative_depth`
- `due_date`
- `available_date`
- `gradable`
- `allow_late_submission`
- `perfect_score`
- `weight`
- `accepts_file_upload`
- `allowed_filetypes`
- `dropbox_multiple`

The normalized item contract intentionally excludes raw free-form item data,
assessment question definitions, passwords, and embedded content payloads.

### Manifest

Represents a bounded, depth-first course content tree summary.

Required fields:

- `entityid`
- `schema_version`
- `version`
- `resourceentityid`
- `count`
- `total_count`
- `limit`
- `truncated`
- `items`

Each manifest item includes stable tree/navigation fields:

- `id`
- `title`
- `type`
- `parentid`
- `sequence`
- `depth`
- `path`
- `child_count`
- `partial`

### Question

Represents an assessment or activity question.

Required fields:

- `questionid`
- `body`
- `interaction_type`
- `choices`

### Submission

Represents a submitted attempt or assignment package.

Required fields:

- `enrollmentid`
- `itemid`
- `activity`
- `student_attachments`
- `q_and_a_pairs`

### Attachment

Represents a submitted file or external document link.

Required fields:

- `name`
- `path`
- `type`
- `source`
- `download_url`

## ID Policy

The server must use explicit Buzz IDs in tool inputs. Opaque convenience IDs may
be accepted only if they decode into the required Buzz IDs.
