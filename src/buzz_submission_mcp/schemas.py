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


def schema(value: dict[str, Any]) -> dict[str, Any]:
    """Return a defensive copy for FastMCP registration."""

    return deepcopy(value)
