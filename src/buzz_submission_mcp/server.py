from __future__ import annotations

from typing import Any, Literal

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - compatibility with older MCP SDK layouts.
    from mcp.server.fastmcp import FastMCP

from .buzz_client import BuzzApiError
from .schemas import (
    ACTIVITY_LIST_SCHEMA,
    ACTIVITY_SCHEMA,
    ATTACHMENT_URL_SCHEMA,
    SUBMISSION_REPORT_SCHEMA,
    schema,
)
from .service import BuzzReadService

mcp = FastMCP("agilix-buzz")


def _service() -> BuzzReadService:
    return BuzzReadService()


@mcp.tool(
    name="buzz.get_activity",
    title="Get Buzz Activity",
    description="Fetch normalized metadata for a Buzz activity item.",
    output_schema=schema(ACTIVITY_SCHEMA),
)
def get_activity(entityid: str, itemid: str) -> dict[str, Any]:
    """Fetch normalized metadata for a Buzz course activity."""

    return _service().get_activity(entityid=entityid, itemid=itemid)


@mcp.tool(
    name="buzz.list_activities",
    title="List Buzz Activities",
    description="Fetch normalized metadata for every activity item in a Buzz course.",
    output_schema=schema(ACTIVITY_LIST_SCHEMA),
)
def list_activities(entityid: str) -> dict[str, Any]:
    """Fetch normalized metadata for Buzz course activity items."""

    return _service().list_activities(entityid=entityid)


@mcp.tool(
    name="buzz.get_submission_report",
    title="Get Buzz Submission Report",
    description=(
        "Fetch a human-readable Buzz student submission report with resolved "
        "activity metadata, question text, answer text, and attachment URLs."
    ),
    output_schema=schema(SUBMISSION_REPORT_SCHEMA),
)
def get_submission_report(
    submissionid: str | None = None,
    enrollmentid: str | None = None,
    itemid: str | None = None,
    entityid: str | None = None,
) -> dict[str, Any]:
    """Return a normalized Buzz student submission report."""

    try:
        return _service().get_submission_report(
            submissionid=submissionid,
            enrollmentid=enrollmentid,
            itemid=itemid,
            entityid=entityid,
        )
    except BuzzApiError:
        raise
    except Exception as exc:
        raise BuzzApiError(f"Failed to build submission report: {exc}") from exc


@mcp.tool(
    name="buzz.get_attachment_url",
    title="Get Buzz Attachment URL",
    description="Build an authenticated Buzz download URL for a submission attachment.",
    output_schema=schema(ATTACHMENT_URL_SCHEMA),
)
def get_attachment_url(
    enrollmentid: str,
    itemid: str,
    filepath: str,
    source: Literal["submission", "attempt-question"] = "submission",
    partid: str | None = None,
) -> dict[str, Any]:
    """Build an authenticated URL for a known Buzz attachment path."""

    return _service().get_attachment_url(
        enrollmentid=enrollmentid,
        itemid=itemid,
        filepath=filepath,
        source=source,
        partid=partid,
    )


@mcp.tool(
    name="get_complete_submission_report",
    title="Get Complete Buzz Submission Report",
    description="Backward-compatible alias for buzz.get_submission_report.",
    output_schema=schema(SUBMISSION_REPORT_SCHEMA),
)
def get_complete_submission_report(
    submissionid: str | None = None,
    enrollmentid: str | None = None,
    itemid: str | None = None,
    entityid: str | None = None,
) -> dict[str, Any]:
    """Return a human-readable Buzz student submission report.

    Resolves the item/assignment/custom-activity title, maps every question's
    choice/order/match IDs into readable answer text via ListQuestions, and
    builds authenticated download URLs for any submitted attachments (e.g.
    PDFs uploaded to an assignment dropbox or to a fileupload question).
    """

    return get_submission_report(
        submissionid=submissionid,
        enrollmentid=enrollmentid,
        itemid=itemid,
        entityid=entityid,
    )


@mcp.resource(
    "buzz://course/{entityid}/item/{itemid}",
    name="buzz.activity",
    title="Buzz Activity",
    description="Normalized metadata for a Buzz activity item.",
    mime_type="application/json",
)
def activity_resource(entityid: str, itemid: str) -> dict[str, Any]:
    return get_activity(entityid=entityid, itemid=itemid)


@mcp.resource(
    "buzz://course/{entityid}/manifest",
    name="buzz.course_manifest",
    title="Buzz Course Manifest",
    description="Normalized metadata for every activity item in a Buzz course.",
    mime_type="application/json",
)
def course_manifest_resource(entityid: str) -> dict[str, Any]:
    return list_activities(entityid=entityid)


@mcp.resource(
    "buzz://submission/{enrollmentid}/{itemid}/report{?entityid}",
    name="buzz.submission_report",
    title="Buzz Submission Report",
    description="Normalized human-readable report for a Buzz student submission.",
    mime_type="application/json",
)
def submission_report_resource(
    enrollmentid: str, itemid: str, entityid: str = ""
) -> dict[str, Any]:
    return get_submission_report(
        enrollmentid=enrollmentid,
        itemid=itemid,
        entityid=entityid,
    )


@mcp.prompt(
    name="buzz.summarize_submission",
    title="Summarize Buzz Submission",
    description="Guide an assistant to summarize a Buzz submission report.",
)
def summarize_submission(enrollmentid: str, itemid: str, entityid: str) -> str:
    return (
        "Summarize the Buzz submission for a teacher. First call "
        "`buzz.get_submission_report` with "
        f"`enrollmentid={enrollmentid}`, `itemid={itemid}`, and "
        f"`entityid={entityid}`. Focus on submitted work, missing answers, "
        "attachments, and anything the teacher should inspect manually. Do not "
        "invent grades or feedback."
    )


@mcp.prompt(
    name="buzz.draft_student_feedback",
    title="Draft Buzz Student Feedback",
    description="Guide an assistant to draft teacher-reviewable feedback.",
)
def draft_student_feedback(enrollmentid: str, itemid: str, entityid: str) -> str:
    return (
        "Draft concise student feedback from a Buzz submission report. First call "
        "`buzz.get_submission_report` with "
        f"`enrollmentid={enrollmentid}`, `itemid={itemid}`, and "
        f"`entityid={entityid}`. Keep feedback evidence-based, reference the "
        "student's submitted answers or attachments, and leave final grading "
        "decisions to the teacher."
    )


@mcp.prompt(
    name="buzz.troubleshoot_submission_access",
    title="Troubleshoot Buzz Submission Access",
    description="Guide support staff through read-only submission access checks.",
)
def troubleshoot_submission_access(enrollmentid: str, itemid: str, entityid: str) -> str:
    return (
        "Troubleshoot Buzz submission access without making changes. Verify the "
        "provided IDs, call `buzz.get_activity`, then call "
        "`buzz.get_submission_report`. Explain whether the failure looks like a "
        "missing ID, unsupported activity type, missing submission, expired "
        "credentials, or insufficient Buzz rights."
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
