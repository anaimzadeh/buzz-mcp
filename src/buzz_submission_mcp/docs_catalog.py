from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .buzz_client import BuzzApiError


DocEntryType = Literal["command", "schema", "enum", "concept"]
DocEntryFilter = Literal["any", "command", "schema", "enum", "concept"]

DOCS_ENTRY_BASE_URL = "https://api.agilixbuzz.com/docs/entry"


@dataclass(frozen=True)
class BuzzDocEntry:
    entry_type: DocEntryType
    name: str
    title: str
    path: str
    summary: str
    category: str
    current_status: str = "current"
    method: str = "/cmd"
    read_only: bool = True
    sensitive: bool = False
    related: tuple[str, ...] = ()
    mcp_phase: str = "documentation-aware read model"
    mcp_relevance: str = "medium"
    notes: tuple[str, ...] = ()

    @property
    def source_url(self) -> str:
        return f"{DOCS_ENTRY_BASE_URL}/{self.path}"

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_type": self.entry_type,
            "name": self.name,
            "title": self.title,
            "path": self.path,
            "source_url": self.source_url,
            "summary": self.summary,
            "category": self.category,
            "current_status": self.current_status,
            "method": self.method,
            "read_only": self.read_only,
            "sensitive": self.sensitive,
            "related": list(self.related),
            "mcp_phase": self.mcp_phase,
            "mcp_relevance": self.mcp_relevance,
            "notes": list(self.notes),
        }


def _command(
    name: str,
    *,
    category: str,
    summary: str,
    related: tuple[str, ...] = (),
    read_only: bool = True,
    sensitive: bool = False,
    phase: str = "documentation-aware read model",
    relevance: str = "high",
    notes: tuple[str, ...] = (),
) -> BuzzDocEntry:
    return BuzzDocEntry(
        entry_type="command",
        name=name,
        title=name,
        path=f"Command/{name}",
        summary=summary,
        category=category,
        read_only=read_only,
        sensitive=sensitive,
        related=related,
        mcp_phase=phase,
        mcp_relevance=relevance,
        notes=notes,
    )


def _schema(
    name: str,
    *,
    category: str,
    summary: str,
    related: tuple[str, ...] = (),
    sensitive: bool = False,
    relevance: str = "medium",
) -> BuzzDocEntry:
    return BuzzDocEntry(
        entry_type="schema",
        name=name,
        title=name,
        path=f"Schema/{name}",
        summary=summary,
        category=category,
        current_status="current",
        method="schema",
        read_only=True,
        sensitive=sensitive,
        related=related,
        mcp_relevance=relevance,
    )


def _enum(
    name: str,
    *,
    category: str,
    summary: str,
    related: tuple[str, ...] = (),
    relevance: str = "medium",
) -> BuzzDocEntry:
    return BuzzDocEntry(
        entry_type="enum",
        name=name,
        title=name,
        path=f"Enum/{name}",
        summary=summary,
        category=category,
        current_status="current",
        method="enum",
        read_only=True,
        related=related,
        mcp_relevance=relevance,
    )


def _concept(
    path: str,
    *,
    title: str,
    category: str,
    summary: str,
    related: tuple[str, ...] = (),
    relevance: str = "medium",
) -> BuzzDocEntry:
    return BuzzDocEntry(
        entry_type="concept",
        name=title,
        title=title,
        path=f"Concept/{path}",
        summary=summary,
        category=category,
        current_status="current",
        method="concept",
        read_only=True,
        related=related,
        mcp_relevance=relevance,
    )


DOC_ENTRIES: tuple[BuzzDocEntry, ...] = (
    _command(
        "GetStudentSubmission",
        category="Submissions",
        summary="Fetch the recursive submission package for an enrollment and item.",
        related=("Submission", "AttemptQuestion", "GetAttemptFile"),
        sensitive=True,
        phase="current PoC",
        notes=("Authenticated file URLs derived from this command include tokens.",),
    ),
    _command(
        "GetItem",
        category="Manifests and Items",
        summary="Fetch one manifest item and its item data.",
        related=("ItemData", "ItemType", "GetItemList"),
        phase="current PoC",
    ),
    _command(
        "GetItemList",
        category="Manifests and Items",
        summary="Fetch visible manifest items for a course or a specific item.",
        related=("ItemData", "ItemType", "GetItem"),
        phase="current PoC",
    ),
    _command(
        "ListQuestions",
        category="Assessments",
        summary="Fetch reusable question definitions for resolving submitted answers.",
        related=("Question", "GetQuestion"),
        phase="current PoC",
    ),
    _command(
        "GetAttemptFile",
        category="Submissions",
        summary="Download a submitted file associated with an attempt question.",
        related=("Submission", "AttemptQuestion"),
        sensitive=True,
        phase="current PoC",
        notes=("Do not expose token-bearing URLs in resource identifiers or logs.",),
    ),
    _command(
        "GetCourse2",
        category="Courses",
        summary="Fetch a current course/entity record.",
        related=("Course", "ListCourses"),
        phase="core entity graph",
    ),
    _command(
        "ListCourses",
        category="Courses",
        summary="List courses visible to the caller, with filtering before broad use.",
        related=("Course", "GetCourse2"),
        phase="core entity graph",
    ),
    _command(
        "GetEnrollment3",
        category="Enrollments",
        summary="Fetch a current enrollment record joining a user to an entity.",
        related=("Enrollment", "User", "Course"),
        sensitive=True,
        phase="core entity graph",
    ),
    _command(
        "ListUserEnrollments",
        category="Enrollments",
        summary="List enrollment records for one user.",
        related=("Enrollment", "User", "Course"),
        sensitive=True,
        phase="core entity graph",
    ),
    _command(
        "ListEntityEnrollments",
        category="Enrollments",
        summary="List enrollment records for one course/entity; roster data is sensitive.",
        related=("Enrollment", "User", "Course"),
        sensitive=True,
        phase="core entity graph",
    ),
    _command(
        "ListEnrollments",
        category="Enrollments",
        summary="List enrollment records with explicit filters.",
        related=("Enrollment", "User", "Course"),
        sensitive=True,
        phase="core entity graph",
    ),
    _command(
        "GetManifest",
        category="Manifests and Items",
        summary="Fetch the course content tree.",
        related=("ItemData", "GetItem", "GetItemList"),
        phase="course content graph",
    ),
    _command(
        "Search2",
        category="Manifests and Items",
        summary="Search course content and return bounded result summaries.",
        related=("Resource", "ItemData"),
        phase="course content graph",
    ),
    _command(
        "GetQuestion",
        category="Assessments",
        summary="Fetch one question definition.",
        related=("Question", "ListQuestions"),
        phase="course content graph",
    ),
    _command(
        "GetAttempt",
        category="Assessments",
        summary="Fetch one student assessment attempt.",
        related=("AttemptQuestion", "Submission"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetAttemptReview",
        category="Assessments",
        summary="Fetch assessment attempt review data for teacher/student review.",
        related=("AttemptQuestion", "Question"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetEnrollmentGradebook2",
        category="Gradebook",
        summary="Fetch item-level and rolled-up grades for one enrollment.",
        related=("Gradebook", "Grades", "Grade"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetUserGradebook2",
        category="Gradebook",
        summary="Fetch gradebook views across a user's enrollments.",
        related=("Gradebook", "Grades", "Enrollment"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetEntityGradebook3",
        category="Gradebook",
        summary="Fetch class/entity gradebook data; high privacy and payload risk.",
        related=("Gradebook", "Grades", "Enrollment"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetGradebookSummary",
        category="Gradebook",
        summary="Fetch summarized gradebook status.",
        related=("Gradebook", "Grade"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetGradeHistory",
        category="Gradebook",
        summary="Fetch grade change history for audit workflows.",
        related=("Grade", "Enrollment"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetStudentSubmissionInfo",
        category="Submissions",
        summary="Fetch lightweight submission state before requesting the full package.",
        related=("Submission", "GetStudentSubmission"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetStudentSubmissionHistory",
        category="Submissions",
        summary="Fetch submission history for support and audit workflows.",
        related=("Submission", "GetStudentSubmission"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetWorkInProgress2",
        category="Submissions",
        summary="Fetch draft work-in-progress state.",
        related=("Submission", "WorkInProgress"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetTeacherResponse",
        category="Submissions",
        summary="Fetch teacher response or feedback package.",
        related=("TeacherResponse", "Submission"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "GetTeacherResponseInfo",
        category="Submissions",
        summary="Fetch lightweight teacher response metadata.",
        related=("TeacherResponse", "Submission"),
        sensitive=True,
        phase="gradebook and submission state",
    ),
    _command(
        "PutTeacherResponse",
        category="Submissions",
        summary="Write teacher feedback; out of current read-only PoC scope.",
        related=("TeacherResponse", "Submission"),
        read_only=False,
        sensitive=True,
        phase="controlled writes",
        relevance="future",
        notes=("Requires dedicated safety spec, confirmation, and audit logging.",),
    ),
    _command(
        "GetEffectiveRights",
        category="Rights",
        summary="Fetch effective rights for diagnostics.",
        related=("RightsFlags", "Role"),
        sensitive=True,
        phase="rights diagnostics",
        relevance="medium",
    ),
    _command(
        "GetActorRights",
        category="Rights",
        summary="Fetch direct actor rights for diagnostics.",
        related=("RightsFlags", "Role"),
        sensitive=True,
        phase="rights diagnostics",
        relevance="medium",
    ),
    _command(
        "GetRightsList",
        category="Rights",
        summary="List rights records for diagnostics and administration.",
        related=("RightsFlags", "Role"),
        sensitive=True,
        phase="rights diagnostics",
        relevance="medium",
    ),
    _schema(
        "Course",
        category="Course Structure",
        summary="Course-like entity with title, type, dates, base course, and flags.",
        related=("GetCourse2", "ListCourses"),
        relevance="high",
    ),
    _schema(
        "User",
        category="Identity And Access",
        summary="Person account in a userspace/domain; redact unnecessary PII.",
        related=("GetUser2", "ListUsers", "Enrollment"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "Enrollment",
        category="Course Structure",
        summary="User-to-entity relationship with role, status, and dates.",
        related=("GetEnrollment3", "ListUserEnrollments", "ListEntityEnrollments"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "ItemData",
        category="Course Structure",
        summary="Activity/content node metadata inside a manifest.",
        related=("GetItem", "GetItemList", "ItemType"),
        relevance="high",
    ),
    _schema(
        "Submission",
        category="Assessment And Submission Work",
        summary="Recursive package of assignment, homework, SCO, and attempt data.",
        related=("GetStudentSubmission", "GetStudentSubmissionInfo"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "Question",
        category="Assessment And Submission Work",
        summary="Reusable assessment question definition.",
        related=("ListQuestions", "GetQuestion"),
        relevance="high",
    ),
    _schema(
        "AttemptQuestion",
        category="Assessment And Submission Work",
        summary="Question instance/version inside a student attempt.",
        related=("GetAttempt", "GetAttemptReview", "Question"),
        sensitive=True,
    ),
    _schema(
        "Grade",
        category="Gradebook And Progress",
        summary="Score/status for one enrollment and item.",
        related=("GetEnrollmentGradebook2", "GetGradeHistory"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "Grades",
        category="Gradebook And Progress",
        summary="Nested gradebook rollups for course, category, period, and items.",
        related=("GetEnrollmentGradebook2", "GetUserGradebook2"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "TeacherResponse",
        category="Assessment And Submission Work",
        summary="Teacher feedback/response package for submitted work.",
        related=("GetTeacherResponse", "PutTeacherResponse"),
        sensitive=True,
    ),
    _schema(
        "Attachment",
        category="Assessment And Submission Work",
        summary="File, Google Drive doc, or media reference inside a submission.",
        related=("GetStudentSubmission", "GetAttemptFile", "Submission"),
        sensitive=True,
        relevance="high",
    ),
    _schema(
        "Resource",
        category="Course Structure",
        summary="File or content asset referenced by items.",
        related=("GetResource", "GetResourceInfo2", "ItemData"),
    ),
    _enum(
        "ItemType",
        category="Course Structure",
        summary="Known item/activity type values used in manifest item data.",
        related=("ItemData", "GetItem"),
        relevance="high",
    ),
    _enum(
        "RightsFlags",
        category="Identity And Access",
        summary="Bit flags and values used to evaluate Buzz permissions.",
        related=("GetEffectiveRights", "GetActorRights", "Role"),
    ),
    _enum(
        "ObjectiveSetFlags",
        category="Gradebook And Progress",
        summary="Flags used by objective and mastery data.",
        related=("Objective",),
    ),
    _enum(
        "MapFlags",
        category="Gradebook And Progress",
        summary="Flags used by objective map relationships.",
        related=("Objective",),
    ),
    _concept(
        "Overview",
        title="Overview",
        category="Documentation Ontology",
        summary="Top-level Buzz documentation overview and navigation shell.",
        related=("Command", "Schema", "Enum"),
    ),
    _concept(
        "EntityIds",
        title="EntityIds",
        category="Course Structure",
        summary="Shared identifier model for courses, sections, groups, and containers.",
        related=("Course", "Enrollment", "GetEntityType"),
        relevance="high",
    ),
    _concept(
        "DataStream",
        title="DataStream",
        category="Collaboration And Content Channels",
        summary="Event stream configuration and emitted domain events.",
        related=("DataStreams",),
        relevance="future",
    ),
)


def search_docs(
    *,
    query: str = "",
    entry_type: DocEntryFilter = "any",
    limit: int = 10,
) -> dict[str, object]:
    _validate_entry_type(entry_type)
    _validate_limit(limit)

    terms = _terms(query)
    results: list[tuple[int, BuzzDocEntry]] = []
    for position, entry in enumerate(DOC_ENTRIES):
        if entry_type != "any" and entry.entry_type != entry_type:
            continue
        score = _match_score(entry, terms)
        if score is not None:
            results.append((score * 1000 - position, entry))

    results.sort(key=lambda item: item[0], reverse=True)
    entries = [entry.to_dict() for _, entry in results[:limit]]
    return {"query": query, "count": len(entries), "results": entries}


def get_command_entry(name: str) -> dict[str, object]:
    return _get_named_entry(name, "command").to_dict()


def get_schema_entry(name: str) -> dict[str, object]:
    return _get_named_entry(name, "schema").to_dict()


def _get_named_entry(name: str, entry_type: DocEntryType) -> BuzzDocEntry:
    normalized = _normalize(name)
    for entry in DOC_ENTRIES:
        if entry.entry_type == entry_type and _normalize(entry.name) == normalized:
            return entry
    raise BuzzApiError(
        f"Unknown Buzz docs {entry_type}: {name}",
        code="INVALID_ID",
        details={"entry_type": entry_type, "name": name},
    )


def _match_score(entry: BuzzDocEntry, terms: list[str]) -> int | None:
    if not terms:
        return _base_score(entry)

    haystack = " ".join(
        (
            entry.entry_type,
            entry.name,
            entry.title,
            entry.path,
            entry.summary,
            entry.category,
            entry.mcp_phase,
            entry.mcp_relevance,
            " ".join(entry.related),
            " ".join(entry.notes),
        )
    ).lower()
    if not all(term in haystack for term in terms):
        return None

    score = _base_score(entry)
    normalized_query = "".join(terms)
    if _normalize(entry.name) == normalized_query:
        score += 8
    if normalized_query in _normalize(entry.name):
        score += 4
    if any(term in entry.name.lower() for term in terms):
        score += 2
    return score


def _base_score(entry: BuzzDocEntry) -> int:
    score = {
        "high": 5,
        "medium": 3,
        "future": 1,
    }.get(entry.mcp_relevance, 2)
    if entry.mcp_phase == "current PoC":
        score += 4
    if entry.entry_type == "command":
        score += 1
    return score


def _terms(query: str) -> list[str]:
    return [term for term in query.lower().replace("_", " ").replace("-", " ").split()]


def _normalize(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _validate_entry_type(entry_type: str) -> None:
    if entry_type not in {"any", "command", "schema", "enum", "concept"}:
        raise BuzzApiError(
            "entry_type must be one of: any, command, schema, enum, concept.",
            code="INVALID_ID",
            details={"field": "entry_type", "value": entry_type},
        )


def _validate_limit(limit: int) -> None:
    if limit < 1 or limit > 50:
        raise BuzzApiError(
            "limit must be between 1 and 50.",
            code="INVALID_ID",
            details={"field": "limit", "value": limit},
        )
