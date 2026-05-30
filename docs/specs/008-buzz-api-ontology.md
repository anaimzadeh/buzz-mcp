# Buzz API Documentation Ontology

## Status

Partially implemented as a local, credential-free documentation catalog with
read-only MCP metadata tools.

## Sources

This ontology is based on the public Buzz documentation app at
`https://api.agilixbuzz.com/docs/#!/Concept/Overview`, inspected on
2026-05-29.

The docs page is a JavaScript shell. Its table of contents is loaded from
`https://api.agilixbuzz.com/docs/toc`, and each clickable table-of-contents
entry resolves through `https://api.agilixbuzz.com/docs/entry/{path}`. In the
DOM, expandable/collapsed list items are rendered from this TOC tree; child
links carry `data-path` values such as `Command/GetStudentSubmission`,
`Schema/Submission`, and `Enum/ItemType`.

The source catalog contains:

| Entry type | Count | Notes |
| --- | ---: | --- |
| Concepts | 89 | Conceptual guides, DataStream event docs, security, rate limiting, and data model pages. |
| Current commands | 263 | Active DLAP command pages. |
| Obsolete commands | 19 | Historical commands that should not drive new MCP tools. |
| Schemas | 36 | XML-shaped domain schemas used by commands. |
| Enumerations | 37 | Flags, statuses, item types, roles, and scoring-related enums. |

## Documentation Ontology

The documentation itself has a stable ontology that can be used for automated
indexing:

| Class | Meaning | Key fields |
| --- | --- | --- |
| `DocEntry` | Any routed documentation page. | `path`, `title`, `category_path`, `source_url` |
| `ConceptTopic` | Narrative topic or workflow guide. | `path`, `title`, `summary`, `links` |
| `Command` | RPC command exposed through `/cmd`. | `name`, `category`, `current_status`, `method`, `rights`, `request`, `response`, `examples`, `see_also` |
| `RequestParameter` | Query/body field accepted by a command. | `name`, `type`, `required`, `allowed_values`, `description` |
| `ResponseNode` | XML/JSON response node declared by a command. | `name`, `type`, `repeat`, `attributes`, `children` |
| `Schema` | Reusable XML-shaped object format. | `name`, `root_node`, `attributes`, `child_nodes`, `see_also` |
| `Enum` | Named set of values or bit flags. | `name`, `values`, `code_format`, `see_also` |
| `RightsRule` | Permission expression needed for a command. | `expression`, `target_id_parameter`, `fallback_owner_rule` |

Important implementation detail: Buzz is RPC-over-HTTP. A `Command` is not a
REST resource; it is a `cmd={lowercasecommand}` request to `/cmd`, often with
XML-shaped JSON output.

## Domain Ontology

### Identity And Access

| Concept | Buzz docs anchor | Description |
| --- | --- | --- |
| `Session` | `Login3`, `Logout`, `ExtendSession` | Authenticated context and token lifecycle. |
| `User` | `Schema/User`, `GetUser2`, `ListUsers` | Person account in a userspace/domain. |
| `Domain` | `Schema/Domain`, `GetDomain2`, `ListDomains` | Tenant or tenant subtree. |
| `Role` | `Schema/Role`, `GetRole`, `ListRoles` | Named privilege bundle. |
| `Rights` | `GetRights`, `GetEffectiveRights`, `RightsFlags` | Permissions applied to actors and targets. |
| `Subscription` | `GetSubscriptionList`, `GetEffectiveSubscriptionList` | Delegated relationship granting access. |
| `CommandToken` | `CreateCommandTokens`, `RedeemCommandToken` | Scoped token for command execution. |

Relationships:

- A `Domain` owns `User`, `Course`, `Group`, `ObjectiveSet`, and resource
  namespaces.
- A `User` authenticates into a `Session`.
- A `Role` aggregates rights; `Rights` and `Subscription` determine what a
  session may read or mutate.
- Rights are command-specific and usually target IDs such as `domainid`,
  `entityid`, `enrollmentid`, or `userid`.

### Course Structure

| Concept | Buzz docs anchor | Description |
| --- | --- | --- |
| `Course` | `Schema/Course`, `GetCourse2`, `ListCourses` | Course-like entity with title, type, dates, base course, and flags. |
| `Entity` | `Concept/EntityIds`, `GetEntityType` | Shared identifier model for courses, sections, groups, and related containers. |
| `Enrollment` | `Schema/Enrollment`, `GetEnrollment3`, list enrollment commands | User-to-entity relationship with role/status/dates. |
| `Group` | `Schema/Group`, group commands | Group within a domain/course context. |
| `Manifest` | `GetManifest`, `GetManifestInfo`, `GetManifestData` | Course content tree. |
| `Item` | `Schema/ItemData`, `ItemType`, item commands | Activity/content node in a manifest. |
| `Resource` | `GetResource`, `GetResourceInfo2`, resource commands | File or content asset referenced by items. |

Relationships:

- A `Course` is an `Entity`.
- A `Course` has one `Manifest`.
- A `Manifest` contains ordered `Item` nodes.
- An `Item` has `ItemData`, an `ItemType`, optional `Resource` references, and
  optional gradebook fields.
- A `User` has many `Enrollment` records.
- An `Enrollment` links a `User` to a `Course` or other `Entity`.

### Assessment And Submission Work

| Concept | Buzz docs anchor | Description |
| --- | --- | --- |
| `Question` | `Schema/Question`, `ListQuestions`, `GetQuestion` | Reusable assessment question definition. |
| `AttemptQuestion` | `Schema/AttemptQuestion` | Question instance/version inside an attempt. |
| `Attempt` | `GetAttempt`, `GetAttemptReview`, attempt commands | Student assessment attempt state. |
| `Submission` | `Schema/Submission`, submission commands | Recursive package of assignment/homework/SCO/attempt data. |
| `WorkInProgress` | `GetWorkInProgress2`, WIP commands | Draft submission state. |
| `TeacherResponse` | `GetTeacherResponse`, `PutTeacherResponse` | Teacher feedback/response package. |
| `Attachment` | `GetStudentSubmission`, `GetAttemptFile` | File, Google Drive doc, or media reference inside a submission. |

Relationships:

- An `Item` of type assessment/homework/assignment can produce `Attempt` and
  `Submission` data.
- A `Submission` is scoped by `enrollmentid` and `itemid`.
- A `Submission` can be recursive: it may contain nested submissions for
  attempts, question answers, homework groups, and peer responses.
- A question submission points to an `AttemptQuestion`, which identifies the
  `Question` and version.
- Attachments are not stable public resources; download URLs are authenticated,
  token-bearing command URLs and must be treated as sensitive.

### Gradebook And Progress

| Concept | Buzz docs anchor | Description |
| --- | --- | --- |
| `Gradebook` | `GetEnrollmentGradebook2`, `GetUserGradebook2`, `GetEntityGradebook3` | Rolled-up and item-level grade view. |
| `Grade` | `Schema/Grade`, `GetGrade` | Score/status for one enrollment and item. |
| `Grades` | `Schema/Grades` | Nested rollups: final, periods, categories, and items. |
| `EnrollmentMetrics` | `Schema/EnrollmentMetrics`, metrics commands | Pace, performance, responsiveness, and completion metrics. |
| `Activity` | `GetEnrollmentActivity`, DataStream activity events | Time and usage events. |
| `Objective` | objective commands, `ObjectiveSetFlags`, `MapFlags` | Learning-objective mastery and mappings. |
| `Badge` | badge commands | Award/assertion records tied to completion. |

Relationships:

- `Gradebook` is scoped by `Enrollment`, `User`, or `Entity`.
- `Grade` is scoped by `Enrollment` plus `Item`.
- `Grades` may contain rollups for course, category, period, and individual
  item scores.
- `EnrollmentMetrics` and `Activity` are read models over a student's work and
  course engagement.

### Collaboration And Content Channels

| Concept | Buzz docs anchor | Description |
| --- | --- | --- |
| `Announcement` | announcement commands | Course/domain announcement content. |
| `Message` | discussion board commands, `Schema/Message` | Discussion post/thread content. |
| `Blog` | blog commands | Blog posts and summaries. |
| `WikiPage` | wiki commands | Wiki page content. |
| `Mail` | `Schema/Mail`, `SendMail` | Mail/message composition target. |
| `Report` | report commands | Runnable report metadata and execution. |
| `DataStream` | DataStream concepts and commands | Event stream configuration and emitted domain events. |

## Command Family Inventory

Current command families, classified by command-name prefix:

| Family | Commands | Read-ish | Non-read/action-ish | MCP relevance |
| --- | ---: | ---: | ---: | --- |
| Gradebook | 20 | 20 | 0 | High: read-only grade and progress views. |
| Manifests and Items | 20 | 12 | 8 | High: course content, activities, search. |
| Authentication | 19 | 3 | 16 | Required internally; not a broad MCP surface. |
| Rights | 18 | 11 | 7 | Medium: diagnostics/admin, sensitive. |
| Assessments | 17 | 10 | 7 | High for question resolution; writes later. |
| Objectives | 16 | 8 | 8 | Medium: mastery and standards workflows. |
| Resources | 15 | 8 | 7 | Medium/high: content retrieval; writes later. |
| Submissions | 15 | 7 | 8 | High: current PoC center. |
| Enrollments | 14 | 9 | 5 | High: joins user/course/submission/gradebook. |
| Domains | 12 | 8 | 4 | Medium: tenant discovery/admin. |
| Users | 12 | 8 | 4 | High for support workflows; privacy-sensitive. |
| Courses | 10 | 2 | 8 | High for discovery; writes later. |
| Discussion Boards | 10 | 3 | 7 | Later collaboration surface. |
| Announcements | 9 | 5 | 4 | Later collaboration surface. |
| Groups | 8 | 3 | 5 | Medium: enrollment/group scoping. |
| Wikis | 8 | 3 | 5 | Later content surface. |
| Blogs | 7 | 4 | 3 | Later content surface. |
| Command Tokens | 7 | 3 | 4 | Sensitive admin/auth surface. |
| Badges | 5 | 3 | 2 | Later achievement surface. |
| Peer Grading | 5 | 4 | 1 | Later submission-review extension. |
| General | 4 | 3 | 1 | Diagnostics. |
| Reports | 4 | 3 | 1 | Later analytics surface. |
| Conversion | 3 | 2 | 1 | Import/export; likely out of early MCP scope. |
| Ratings | 3 | 2 | 1 | Later item-feedback surface. |
| DataStreams | 2 | 1 | 1 | Integration/admin, not core read workflow. |

The prefix classifier is approximate. For example, `AssignItem` and
`UnassignItem` are action commands even though they do not start with a common
write prefix.

## Current MCP Mapping

The current server exposes a narrow, read-only slice:

| MCP concept | Tool/resource | Buzz commands |
| --- | --- | --- |
| `Course` | `buzz.get_course`, `buzz.list_courses`, course and domain-courses resources | `GetCourse2`, `ListCourses` |
| `User` | `buzz.get_user`, user resource | `GetUser2` |
| `Enrollment` | `buzz.get_enrollment`, `buzz.list_user_enrollments`, `buzz.list_entity_enrollments`, enrollment resources | `GetEnrollment3`, `ListUserEnrollments`, `ListEntityEnrollments` |
| `Manifest` | `buzz.get_manifest`, manifest summary resource | `GetManifest` |
| `ActivityItem` | `buzz.get_activity`, `buzz.list_activities`, course item resources | `GetItem`, `GetItemList` |
| `Submission` report | `buzz.get_submission_report`, submission report resource | `GetStudentSubmission`, `GetItem`, `GetItemList`, `ListQuestions`, obsolete fallback `GetQuestionList` |
| `Attachment` URL | `buzz.get_attachment_url` | `GetStudentSubmission` with `packagetype=file`, `GetAttemptFile` |
| Docs metadata | `buzz.docs.search`, `buzz.docs.get_command`, `buzz.docs.get_schema` | Local high-value command, schema, enum, and concept catalog |
| Auth session | internal client only | `Login3` |

This maps to the documentation ontology as:

- `Course` -> `Manifest` -> `Item` is partially implemented with a bounded
  manifest summary and lightweight activity views.
- `Enrollment` -> `Submission` -> `Question`/`Attachment` is partially
  implemented.
- `Course`, `User`, and `Enrollment` are first-class MCP outputs.
- `Gradebook` is specified in local docs but not yet a first-class MCP output.

## Recommended MCP Build Sequence

### Phase 1: Documentation-Aware Read Model

Add an internal docs index generated from `docs/toc` and `docs/entry/{path}`.
It should not be a user-facing dependency at runtime, but it can drive tests,
schema design, and implementation priority.

Useful internal records:

- `CommandSpec`: command name, method, parameter list, rights string, response
  root, schema refs, see-also refs.
- `SchemaSpec`: schema root node, attributes, child nodes, enum refs.
- `EnumSpec`: enum values and whether values are flags or names.

The PoC seeds a local high-value docs index and exposes:

- `buzz.docs.search`
- `buzz.docs.get_command`
- `buzz.docs.get_schema`

These are read-only metadata tools and can be useful to assistants that need to
reason about Buzz without guessing command names.

### Phase 2: Core Entity Graph

Add first-class course, user, and enrollment read tools before expanding into
large gradebook or collaboration surfaces.

| Proposed MCP tool | Buzz commands | Output concept | Notes |
| --- | --- | --- | --- |
| `buzz.get_course` | `GetCourse2` | `Course` | Implemented. |
| `buzz.list_courses` | `ListCourses` | `Course[]` | Implemented with explicit nonzero domain ID, current/active scope, text filter, and max limit. |
| `buzz.get_user` | `GetUser2` | `User` | Implemented with default response only and PII-heavy fields omitted. |
| `buzz.get_enrollment` | `GetEnrollment3` | `Enrollment` | Implemented without joined user/entity expansion. |
| `buzz.list_user_enrollments` | `ListUserEnrollments` | `Enrollment[]` | Implemented with service-side limit. |
| `buzz.list_entity_enrollments` | `ListEntityEnrollments` | `Enrollment[]` | Implemented with service-side limit; privacy-sensitive. |

Resource templates:

```text
buzz://course/{entityid}
buzz://domain/{domainid}/courses
buzz://user/{userid}
buzz://enrollment/{enrollmentid}
buzz://course/{entityid}/enrollments
```

### Phase 3: Course Content Graph

Extend the existing activity model into a richer content graph.

| Proposed MCP tool | Buzz commands | Output concept | Notes |
| --- | --- | --- | --- |
| `buzz.get_manifest` | `GetManifest` | `Manifest` | Implemented as a bounded, depth-first summary. |
| `buzz.get_item` | `GetItem` | `Item` | Current `buzz.get_activity` can become a normalized view. |
| `buzz.list_items` | `GetItemList` | `Item[]` | Add `query`, `itemid`, and `allversions` only after validating output size. |
| `buzz.search_course_content` | `Search2` | Search result summaries | Use pagination; prefer links to resource/item details. |
| `buzz.get_resource_info` | `GetResourceInfo2` | `Resource` metadata | Avoid returning raw file contents unless explicitly requested. |

Resource templates:

```text
buzz://course/{entityid}/manifest/raw
buzz://course/{entityid}/manifest/summary
buzz://course/{entityid}/items
buzz://course/{entityid}/item/{itemid}
buzz://course/{entityid}/resource/{resourceid}
```

### Phase 4: Gradebook And Submission State

Keep gradebook reads explicit and scoped. Do not overload the existing
submission report tool with gradebook data.

| Proposed MCP tool | Buzz commands | Output concept | Notes |
| --- | --- | --- | --- |
| `buzz.get_enrollment_gradebook` | `GetEnrollmentGradebook2` | `Gradebook` | Natural first gradebook tool. |
| `buzz.get_user_gradebook` | `GetUserGradebook2` | `Gradebook[]` | Useful for cross-course student views. |
| `buzz.get_entity_gradebook` | `GetEntityGradebook3` | class gradebook | Higher privacy and payload risk. |
| `buzz.get_grade` | `GetGrade` | `Grade` | Docs warn not to loop this; use gradebook commands for bulk reads. |
| `buzz.get_submission_state` | `GetStudentSubmissionInfo` | submission metadata | Lightweight state before full report. |
| `buzz.get_submission_history` | `GetStudentSubmissionHistory` | submission history | Teacher/support audit workflow. |
| `buzz.get_teacher_response` | `GetTeacherResponse` | teacher response package | Read-only feedback retrieval. |

Resource templates:

```text
buzz://enrollment/{enrollmentid}/gradebook
buzz://user/{userid}/gradebook
buzz://course/{entityid}/gradebook
buzz://submission/{enrollmentid}/{itemid}
buzz://submission/{enrollmentid}/{itemid}/history
buzz://submission/{enrollmentid}/{itemid}/teacher-response
```

### Phase 5: Controlled Writes

Writes are out of the current PoC scope. When introduced, they should be
isolated behind specific safety specs and explicit user confirmation.

Candidate write tools:

- `buzz.put_teacher_response`
- `buzz.update_grade`
- `buzz.put_work_in_progress`
- `buzz.submit_work_in_progress`
- `buzz.update_activity_metadata`

Required controls:

- Narrow input schemas; no raw arbitrary XML for general users.
- Preview/dry-run where the API shape allows it.
- Explicit confirmation and audit logs.
- Idempotency guidance for retries.
- Redaction of tokens, signed URLs, student PII, and secret fields.

## Implementation Guidance

- Prefer current command names over obsolete pages: `GetCourse2`,
  `GetEnrollment3`, and `GetEntityGradebook3` instead of older variants.
- Treat non-`OK` response-body codes as API errors even when HTTP status is 200.
- Normalize Buzz XML-shaped JSON carefully. Single nodes and repeated nodes can
  change shape between object and array.
- Preserve the local MCP contract around stable domain concepts; do not expose
  raw DLAP XML as the default tool output.
- Add paging and filtering before exposing list commands with broad scope.
- Use command `select` parameters where documented to minimize PII and payload
  size.
- Keep authenticated file URLs out of resource URIs and logs.
- Map Buzz rights failures into the existing `BuzzApiError` model, preserving
  enough detail for support without exposing credentials or signed URLs.
- Treat `GetGrade` as a single-grade convenience only. For multiple grades, use
  `GetEnrollmentGradebook2`, `GetUserGradebook2`, or `GetEntityGradebook3` as
  recommended by the Buzz docs.

## High-Value Command Anchors

| Workflow | Commands |
| --- | --- |
| Course discovery | `ListCourses`, `GetCourse2` |
| Enrollment graph | `ListUserEnrollments`, `ListEntityEnrollments`, `ListEnrollments`, `GetEnrollment3` |
| Course content | `GetManifest`, `GetItemList`, `GetItem`, `Search2` |
| Assessment/question resolution | `ListQuestions`, `GetQuestion`, `GetAttempt`, `GetAttemptReview` |
| Gradebook | `GetEnrollmentGradebook2`, `GetUserGradebook2`, `GetEntityGradebook3`, `GetGradebookSummary`, `GetGradeHistory` |
| Submissions | `GetStudentSubmission`, `GetStudentSubmissionInfo`, `GetStudentSubmissionHistory`, `GetWorkInProgress2` |
| Teacher feedback | `GetTeacherResponse`, `GetTeacherResponseInfo`, future `PutTeacherResponse` |
| Rights diagnostics | `GetEffectiveRights`, `GetActorRights`, `GetRightsList` |
