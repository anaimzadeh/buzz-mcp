# Resource URIs

## Status

Partially implemented for activity, course, enrollment, enrollment-list, and
submission-report read resources.

## URI Scheme

The official server uses the custom URI scheme `buzz://`.

## PoC Resource Templates

### Submission Report

```text
buzz://submission/{enrollmentid}/{itemid}/report?entityid={entityid}
```

Returns the same normalized JSON contract as `buzz.get_submission_report`.

### Activity

```text
buzz://course/{entityid}/item/{itemid}
```

Returns normalized `ActivityItem` JSON.

### Course Manifest

```text
buzz://course/{entityid}/manifest
```

Returns `entityid`, `count`, and an `activities` array containing normalized
`ActivityItem` JSON.

### Course

```text
buzz://course/{entityid}
```

Returns normalized `Course` JSON.

### Enrollment

```text
buzz://enrollment/{enrollmentid}
```

Returns normalized `Enrollment` JSON.

### User

```text
buzz://user/{userid}
```

Returns privacy-redacted normalized `User` JSON.

### User Enrollments

```text
buzz://user/{userid}/enrollments
```

Returns the same normalized JSON contract as `buzz.list_user_enrollments`.

### Course Enrollments

```text
buzz://course/{entityid}/enrollments
```

Returns the same normalized JSON contract as `buzz.list_entity_enrollments`.

## Rules

- Resource URIs must not include DLAP tokens, passwords, or signed attachment URLs.
- Query parameters must be explicit and documented.
- Resources must not perform write operations.
- Large resources should return summary JSON and link to more specific resources.

## Future Templates

```text
buzz://enrollment/{enrollmentid}/gradebook
buzz://submission/{enrollmentid}/{itemid}
```
