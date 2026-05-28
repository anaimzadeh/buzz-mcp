# Resource URIs

## Status

Draft.

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

## Rules

- Resource URIs must not include DLAP tokens, passwords, or signed attachment URLs.
- Query parameters must be explicit and documented.
- Resources must not perform write operations.
- Large resources should return summary JSON and link to more specific resources.

## Future Templates

```text
buzz://course/{entityid}
buzz://course/{entityid}/manifest
buzz://enrollment/{enrollmentid}/gradebook
buzz://submission/{enrollmentid}/{itemid}
buzz://user/{userid}
```
