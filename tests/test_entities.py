from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.entities import (
    extract_course,
    extract_enrollment,
    extract_enrollments,
    extract_user,
)


COURSE_XML = """
<response code="OK">
  <course
    id="4378"
    title="Algebra I"
    domainid="100"
    reference="ALG-1"
    guid="course-guid"
    baseid="200"
    type="Course"
    startdate="2025-08-01T00:00:00Z"
    enddate="2026-05-30T00:00:00Z"
    days="304"
    term="Fall"
    version="12" />
</response>
"""

ENROLLMENT_XML = """
<response code="OK">
  <enrollment
    id="4317"
    userid="9001"
    courseid="4378"
    domainid="100"
    reference="student-ref"
    guid="enrollment-guid"
    privileges="Student"
    status="1"
    startdate="2025-08-01T00:00:00Z"
    enddate="2026-05-30T00:00:00Z"
    firstactivitydate="2025-08-10T12:00:00Z"
    lastactivitydate="2025-09-01T12:00:00Z"
    version="4" />
</response>
"""

USER_XML = """
<response code="OK">
  <user
    id="9001"
    firstname="Sally"
    lastname="Johnson"
    domainid="100"
    reference="student-ref"
    guid="user-guid"
    username="sally.johnson"
    email="sally.johnson@example.edu"
    lastpasswordchangeddate="2025-01-01T00:00:00Z"
    lastlogindate="2025-09-01T12:00:00Z"
    version="7" />
</response>
"""

ENROLLMENTS_XML = """
<response code="OK">
  <enrollments>
    <enrollment id="4317" userid="9001" courseid="4378" privileges="Student" status="1" />
    <enrollment id="4318" userid="9002" courseid="4378" roleid="Teacher" status="1" />
  </enrollments>
</response>
"""


class EntityParserTests(unittest.TestCase):
    def test_extract_course_returns_stable_contract(self) -> None:
        course = extract_course(COURSE_XML)

        self.assertEqual(course["entityid"], "4378")
        self.assertEqual(course["title"], "Algebra I")
        self.assertEqual(course["type"], "Course")
        self.assertEqual(course["reference"], "ALG-1")
        self.assertEqual(course["start_date"], "2025-08-01T00:00:00Z")

    def test_extract_user_returns_privacy_redacted_contract(self) -> None:
        user = extract_user(USER_XML)

        self.assertEqual(user["id"], "9001")
        self.assertEqual(user["display_name"], "Sally Johnson")
        self.assertEqual(user["reference"], "student-ref")
        self.assertEqual(user["domainid"], "100")
        self.assertEqual(user["version"], "7")
        self.assertTrue(user["pii_redacted"])
        self.assertNotIn("email", user)
        self.assertNotIn("lastlogindate", user)

    def test_extract_user_falls_back_for_display_name(self) -> None:
        user = extract_user(
            '<response code="OK"><user id="9001" username="sjohnson" /></response>'
        )

        self.assertEqual(user["display_name"], "sjohnson")
        self.assertEqual(user["reference"], "")

    def test_extract_enrollment_returns_stable_contract(self) -> None:
        enrollment = extract_enrollment(ENROLLMENT_XML)

        self.assertEqual(enrollment["enrollmentid"], "4317")
        self.assertEqual(enrollment["entityid"], "4378")
        self.assertEqual(enrollment["userid"], "9001")
        self.assertEqual(enrollment["role"], "Student")
        self.assertEqual(enrollment["privileges"], "Student")
        self.assertEqual(enrollment["last_activity_date"], "2025-09-01T12:00:00Z")

    def test_extract_enrollments_accepts_list_response(self) -> None:
        enrollments = extract_enrollments(ENROLLMENTS_XML)

        self.assertEqual(len(enrollments), 2)
        self.assertEqual(enrollments[0]["enrollmentid"], "4317")
        self.assertEqual(enrollments[1]["role"], "Teacher")

    def test_extract_course_rejects_missing_required_fields(self) -> None:
        with self.assertRaises(BuzzApiError) as raised:
            extract_course('<response code="OK"><course id="4378" /></response>')

        self.assertEqual(raised.exception.code, "BUZZ_API_ERROR")
        self.assertEqual(
            raised.exception.details["missing"],
            ["title", "type"],
        )


if __name__ == "__main__":
    unittest.main()
