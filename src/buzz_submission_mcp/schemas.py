from __future__ import annotations

from copy import deepcopy
from typing import Any


STRING = {"type": "string"}

ATTACHMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": STRING,
        "path": STRING,
        "type": STRING,
        "source": {"type": "string", "enum": ["submission", "attempt-question"]},
        "questionid": STRING,
        "partid": STRING,
        "download_url": STRING,
    },
    "required": ["name", "path", "type", "source"],
    "additionalProperties": False,
}

ACTIVITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": STRING,
        "entityid": STRING,
        "title": STRING,
        "type": STRING,
        "abbreviation": STRING,
        "accepts_file_upload": {"type": "boolean"},
        "allowed_filetypes": STRING,
        "dropbox_multiple": {"type": "boolean"},
        "perfect_score": STRING,
        "due_date": STRING,
    },
    "required": [
        "id",
        "title",
        "type",
        "abbreviation",
        "accepts_file_upload",
        "allowed_filetypes",
        "dropbox_multiple",
        "perfect_score",
        "due_date",
    ],
    "additionalProperties": False,
}

ACTIVITY_LIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entityid": STRING,
        "count": {"type": "integer"},
        "activities": {"type": "array", "items": ACTIVITY_SCHEMA},
    },
    "required": ["entityid", "count", "activities"],
    "additionalProperties": False,
}

COURSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entityid": STRING,
        "title": STRING,
        "type": STRING,
        "domainid": STRING,
        "reference": STRING,
        "guid": STRING,
        "baseid": STRING,
        "start_date": STRING,
        "end_date": STRING,
        "days": STRING,
        "term": STRING,
        "version": STRING,
    },
    "required": ["entityid", "title", "type"],
    "additionalProperties": False,
}

COURSE_LIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "domainid": STRING,
        "includedescendantdomains": {"type": "boolean"},
        "show": {"type": "string", "enum": ["current", "active"]},
        "text": STRING,
        "count": {"type": "integer"},
        "limit": {"type": "integer"},
        "courses": {"type": "array", "items": COURSE_SCHEMA},
    },
    "required": [
        "domainid",
        "includedescendantdomains",
        "show",
        "count",
        "limit",
        "courses",
    ],
    "additionalProperties": False,
}

USER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": STRING,
        "display_name": STRING,
        "reference": STRING,
        "domainid": STRING,
        "guid": STRING,
        "version": STRING,
        "pii_redacted": {"type": "boolean"},
    },
    "required": ["id", "display_name", "reference", "pii_redacted"],
    "additionalProperties": False,
}

ENROLLMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "enrollmentid": STRING,
        "entityid": STRING,
        "userid": STRING,
        "role": STRING,
        "roleid": STRING,
        "privileges": STRING,
        "status": STRING,
        "domainid": STRING,
        "reference": STRING,
        "guid": STRING,
        "start_date": STRING,
        "end_date": STRING,
        "first_activity_date": STRING,
        "last_activity_date": STRING,
        "version": STRING,
    },
    "required": ["enrollmentid", "entityid", "userid", "role", "status"],
    "additionalProperties": False,
}

ENROLLMENT_LIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "userid": STRING,
        "entityid": STRING,
        "count": {"type": "integer"},
        "limit": {"type": "integer"},
        "enrollments": {"type": "array", "items": ENROLLMENT_SCHEMA},
    },
    "required": ["count", "limit", "enrollments"],
    "additionalProperties": False,
}

QA_PAIR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": STRING,
        "answer": STRING,
        "interaction_type": STRING,
        "attachments": {"type": "array", "items": ATTACHMENT_SCHEMA},
    },
    "required": ["question", "answer"],
    "additionalProperties": False,
}

SUBMISSION_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "activity_title": STRING,
        "activity": ACTIVITY_SCHEMA,
        "student_attachments": {"type": "array", "items": ATTACHMENT_SCHEMA},
        "q_and_a_pairs": {"type": "array", "items": QA_PAIR_SCHEMA},
    },
    "required": [
        "activity_title",
        "activity",
        "student_attachments",
        "q_and_a_pairs",
    ],
    "additionalProperties": False,
}

ATTACHMENT_URL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "download_url": STRING,
        "source": {"type": "string", "enum": ["submission", "attempt-question"]},
        "filepath": STRING,
        "partid": STRING,
    },
    "required": ["download_url", "source", "filepath"],
    "additionalProperties": False,
}

DOC_ENTRY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entry_type": {
            "type": "string",
            "enum": ["command", "schema", "enum", "concept"],
        },
        "name": STRING,
        "title": STRING,
        "path": STRING,
        "source_url": STRING,
        "summary": STRING,
        "category": STRING,
        "current_status": STRING,
        "method": STRING,
        "read_only": {"type": "boolean"},
        "sensitive": {"type": "boolean"},
        "related": {"type": "array", "items": STRING},
        "mcp_phase": STRING,
        "mcp_relevance": STRING,
        "notes": {"type": "array", "items": STRING},
    },
    "required": [
        "entry_type",
        "name",
        "title",
        "path",
        "source_url",
        "summary",
        "category",
        "current_status",
        "method",
        "read_only",
        "sensitive",
        "related",
        "mcp_phase",
        "mcp_relevance",
        "notes",
    ],
    "additionalProperties": False,
}

DOC_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": STRING,
        "count": {"type": "integer"},
        "results": {"type": "array", "items": DOC_ENTRY_SCHEMA},
    },
    "required": ["query", "count", "results"],
    "additionalProperties": False,
}


def schema(value: dict[str, Any]) -> dict[str, Any]:
    """Return a defensive copy for FastMCP registration."""

    return deepcopy(value)
