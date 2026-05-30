from __future__ import annotations

from typing import Any, Literal

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - compatibility with older MCP SDK layouts.
    from mcp.server.fastmcp import FastMCP

from .buzz_client import BuzzApiError
from .docs_catalog import get_command_entry, get_schema_entry, search_docs
from .schemas import (
    ACTIVITY_LIST_SCHEMA,
    ACTIVITY_SCHEMA,
    ATTACHMENT_URL_SCHEMA,
    COURSE_LIST_SCHEMA,
    COURSE_SCHEMA,
    DOC_ENTRY_SCHEMA,
    DOC_SEARCH_SCHEMA,
    ENROLLMENT_LIST_SCHEMA,
    ENROLLMENT_SCHEMA,
    SUBMISSION_REPORT_SCHEMA,
    USER_SCHEMA,
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
    name="buzz.get_course",
    title="Get Buzz Course",
    description="Fetch normalized metadata for a Buzz course or course-like entity.",
    output_schema=schema(COURSE_SCHEMA),
)
def get_course(courseid: str, version: str | None = None) -> dict[str, Any]:
    """Fetch normalized metadata for a Buzz course."""

    return _service().get_course(courseid=courseid, version=version)


@mcp.tool(
    name="buzz.list_courses",
    title="List Buzz Courses",
    description=(
        "Fetch normalized Buzz course records for an explicit domain. "
        "The tool omits raw query/select expansion and rejects domainid=0."
    ),
    output_schema=schema(COURSE_LIST_SCHEMA),
)
def list_courses(
    domainid: str,
    includedescendantdomains: bool = False,
    show: Literal["current", "active"] = "current",
    text: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Fetch normalized course records for an explicit Buzz domain."""

    return _service().list_courses(
        domainid=domainid,
        includedescendantdomains=includedescendantdomains,
        show=show,
        text=text,
        limit=limit,
    )


@mcp.tool(
    name="buzz.get_user",
    title="Get Buzz User",
    description="Fetch privacy-redacted metadata for a Buzz user.",
    output_schema=schema(USER_SCHEMA),
)
def get_user(userid: str) -> dict[str, Any]:
    """Fetch privacy-redacted metadata for a Buzz user."""

    return _service().get_user(userid=userid)


@mcp.tool(
    name="buzz.get_enrollment",
    title="Get Buzz Enrollment",
    description="Fetch a normalized Buzz enrollment record.",
    output_schema=schema(ENROLLMENT_SCHEMA),
)
def get_enrollment(enrollmentid: str) -> dict[str, Any]:
    """Fetch a normalized Buzz enrollment."""

    return _service().get_enrollment(enrollmentid=enrollmentid)


@mcp.tool(
    name="buzz.list_user_enrollments",
    title="List Buzz User Enrollments",
    description="Fetch normalized Buzz enrollment records for a user.",
    output_schema=schema(ENROLLMENT_LIST_SCHEMA),
)
def list_user_enrollments(
    userid: str,
    entityid: str | None = None,
    allstatus: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """Fetch normalized enrollment records for a Buzz user."""

    return _service().list_user_enrollments(
        userid=userid,
        entityid=entityid,
        allstatus=allstatus,
        limit=limit,
    )


@mcp.tool(
    name="buzz.list_entity_enrollments",
    title="List Buzz Entity Enrollments",
    description="Fetch normalized Buzz enrollment records for a course/entity.",
    output_schema=schema(ENROLLMENT_LIST_SCHEMA),
)
def list_entity_enrollments(
    entityid: str,
    userid: str | None = None,
    allstatus: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """Fetch normalized enrollment records for a Buzz course or entity."""

    return _service().list_entity_enrollments(
        entityid=entityid,
        userid=userid,
        allstatus=allstatus,
        limit=limit,
    )


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


@mcp.tool(
    name="buzz.docs.search",
    title="Search Buzz Documentation",
    description=(
        "Search the local high-value Buzz documentation catalog for commands, "
        "schemas, enums, and concepts relevant to MCP implementation."
    ),
    output_schema=schema(DOC_SEARCH_SCHEMA),
)
def docs_search(
    query: str = "",
    entry_type: Literal["any", "command", "schema", "enum", "concept"] = "any",
    limit: int = 10,
) -> dict[str, Any]:
    """Search local Buzz documentation metadata."""

    return search_docs(query=query, entry_type=entry_type, limit=limit)


@mcp.tool(
    name="buzz.docs.get_command",
    title="Get Buzz Command Documentation",
    description="Return local metadata for a known high-value Buzz DLAP command.",
    output_schema=schema(DOC_ENTRY_SCHEMA),
)
def docs_get_command(name: str) -> dict[str, Any]:
    """Fetch local metadata for a known Buzz command."""

    return get_command_entry(name)


@mcp.tool(
    name="buzz.docs.get_schema",
    title="Get Buzz Schema Documentation",
    description="Return local metadata for a known high-value Buzz schema.",
    output_schema=schema(DOC_ENTRY_SCHEMA),
)
def docs_get_schema(name: str) -> dict[str, Any]:
    """Fetch local metadata for a known Buzz schema."""

    return get_schema_entry(name)


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
    "buzz://course/{entityid}",
    name="buzz.course",
    title="Buzz Course",
    description="Normalized metadata for a Buzz course or course-like entity.",
    mime_type="application/json",
)
def course_resource(entityid: str) -> dict[str, Any]:
    return get_course(courseid=entityid)


@mcp.resource(
    "buzz://domain/{domainid}/courses",
    name="buzz.domain_courses",
    title="Buzz Domain Courses",
    description="Normalized course records for an explicit Buzz domain.",
    mime_type="application/json",
)
def domain_courses_resource(domainid: str) -> dict[str, Any]:
    return list_courses(domainid=domainid)


@mcp.resource(
    "buzz://user/{userid}",
    name="buzz.user",
    title="Buzz User",
    description="Privacy-redacted metadata for a Buzz user.",
    mime_type="application/json",
)
def user_resource(userid: str) -> dict[str, Any]:
    return get_user(userid=userid)


@mcp.resource(
    "buzz://enrollment/{enrollmentid}",
    name="buzz.enrollment",
    title="Buzz Enrollment",
    description="Normalized metadata for a Buzz enrollment.",
    mime_type="application/json",
)
def enrollment_resource(enrollmentid: str) -> dict[str, Any]:
    return get_enrollment(enrollmentid=enrollmentid)


@mcp.resource(
    "buzz://user/{userid}/enrollments",
    name="buzz.user_enrollments",
    title="Buzz User Enrollments",
    description="Normalized enrollment records for a Buzz user.",
    mime_type="application/json",
)
def user_enrollments_resource(userid: str) -> dict[str, Any]:
    return list_user_enrollments(userid=userid)


@mcp.resource(
    "buzz://course/{entityid}/enrollments",
    name="buzz.course_enrollments",
    title="Buzz Course Enrollments",
    description="Normalized enrollment records for a Buzz course/entity.",
    mime_type="application/json",
)
def course_enrollments_resource(entityid: str) -> dict[str, Any]:
    return list_entity_enrollments(entityid=entityid)


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
