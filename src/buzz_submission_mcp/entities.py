from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .buzz_client import BuzzApiError
from .reporting import parse_xml, local_name


def extract_course(course_xml: str) -> dict[str, Any]:
    """Normalize a GetCourse2 response into the MCP Course contract."""

    root = parse_xml(course_xml, "GetCourse2 payload")
    course = _find_first(root, "course")
    if course is None:
        raise BuzzApiError(
            "Response did not include a <course> element.",
            code="NOT_FOUND",
            details={"parser": "extract_course"},
        )
    return course_to_dict(course)


def extract_courses(courses_xml: str) -> list[dict[str, Any]]:
    """Normalize a ListCourses response into MCP Course contracts."""

    root = parse_xml(courses_xml, "ListCourses payload")
    return [
        course_to_dict(element)
        for element in root.iter()
        if local_name(element.tag) in {"course", "_course"}
    ]


def extract_user(user_xml: str) -> dict[str, Any]:
    """Normalize a GetUser2 response into the MCP User contract."""

    root = parse_xml(user_xml, "GetUser2 payload")
    user = _find_first(root, "user")
    if user is None:
        raise BuzzApiError(
            "Response did not include a <user> element.",
            code="NOT_FOUND",
            details={"parser": "extract_user"},
        )
    return user_to_dict(user)


def extract_enrollment(enrollment_xml: str) -> dict[str, Any]:
    """Normalize a GetEnrollment3 response into the MCP Enrollment contract."""

    root = parse_xml(enrollment_xml, "GetEnrollment3 payload")
    enrollment = _find_first(root, "enrollment")
    if enrollment is None:
        raise BuzzApiError(
            "Response did not include an <enrollment> element.",
            code="NOT_FOUND",
            details={"parser": "extract_enrollment"},
        )
    return enrollment_to_dict(enrollment)


def extract_enrollments(enrollments_xml: str) -> list[dict[str, Any]]:
    """Normalize list enrollment responses into MCP Enrollment contracts."""

    root = parse_xml(enrollments_xml, "ListEnrollments payload")
    return [
        enrollment_to_dict(element)
        for element in root.iter()
        if local_name(element.tag) in {"enrollment", "_enrollment"}
    ]


def course_to_dict(course: ET.Element) -> dict[str, Any]:
    entityid = _attr(course, "id", "entityid", "courseid")
    title = _attr(course, "title")
    course_type = _attr(course, "type")
    missing = [
        field
        for field, value in {
            "entityid": entityid,
            "title": title,
            "type": course_type,
        }.items()
        if not value
    ]
    if missing:
        raise BuzzApiError(
            "Course response missing required field(s): " + ", ".join(missing),
            code="BUZZ_API_ERROR",
            details={"parser": "course_to_dict", "missing": missing},
        )

    return {
        "entityid": entityid,
        "title": title,
        "type": course_type,
        "domainid": _attr(course, "domainid"),
        "reference": _attr(course, "reference"),
        "guid": _attr(course, "guid"),
        "baseid": _attr(course, "baseid"),
        "start_date": _attr(course, "startdate"),
        "end_date": _attr(course, "enddate"),
        "days": _attr(course, "days"),
        "term": _attr(course, "term"),
        "version": _attr(course, "version"),
    }


def user_to_dict(user: ET.Element) -> dict[str, Any]:
    userid = _attr(user, "id", "userid")
    display_name = _display_name(user)
    if not userid:
        raise BuzzApiError(
            "User response missing required field: id",
            code="BUZZ_API_ERROR",
            details={"parser": "user_to_dict", "missing": ["id"]},
        )

    return {
        "id": userid,
        "display_name": display_name or userid,
        "reference": _attr(user, "reference"),
        "domainid": _attr(user, "domainid"),
        "guid": _attr(user, "guid"),
        "version": _attr(user, "version"),
        "pii_redacted": True,
    }


def enrollment_to_dict(enrollment: ET.Element) -> dict[str, Any]:
    enrollmentid = _attr(enrollment, "id", "enrollmentid")
    entityid = _attr(enrollment, "entityid", "courseid")
    userid = _attr(enrollment, "userid")
    roleid = _attr(enrollment, "roleid")
    privileges = _attr(enrollment, "privileges")
    role = _attr(enrollment, "role") or roleid or privileges
    status = _attr(enrollment, "status")

    missing = [
        field
        for field, value in {
            "enrollmentid": enrollmentid,
            "entityid": entityid,
            "userid": userid,
            "role": role,
            "status": status,
        }.items()
        if not value
    ]
    if missing:
        raise BuzzApiError(
            "Enrollment response missing required field(s): " + ", ".join(missing),
            code="BUZZ_API_ERROR",
            details={"parser": "enrollment_to_dict", "missing": missing},
        )

    return {
        "enrollmentid": enrollmentid,
        "entityid": entityid,
        "userid": userid,
        "role": role,
        "roleid": roleid,
        "privileges": privileges,
        "status": status,
        "domainid": _attr(enrollment, "domainid"),
        "reference": _attr(enrollment, "reference"),
        "guid": _attr(enrollment, "guid"),
        "start_date": _attr(enrollment, "startdate"),
        "end_date": _attr(enrollment, "enddate"),
        "first_activity_date": _attr(enrollment, "firstactivitydate"),
        "last_activity_date": _attr(enrollment, "lastactivitydate"),
        "version": _attr(enrollment, "version"),
    }


def _find_first(root: ET.Element, name: str) -> ET.Element | None:
    wanted = name.lower()
    for element in root.iter():
        if local_name(element.tag) == wanted:
            return element
    return None


def _attr(element: ET.Element, *names: str) -> str:
    for name in names:
        value = element.attrib.get(name)
        if value:
            return value
    return ""


def _display_name(user: ET.Element) -> str:
    first = _attr(user, "firstname")
    last = _attr(user, "lastname")
    full_name = " ".join(part for part in (first, last) if part).strip()
    return full_name or _attr(user, "username", "reference")
