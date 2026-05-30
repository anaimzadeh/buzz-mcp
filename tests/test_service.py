from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.service import BuzzReadService


SUBMISSION_XML = """
<submission type="attempt">
  <submission type="question" partid="5">
    <attemptquestion questionid="q-choice" />
    <answer>2</answer>
  </submission>
  <attachments>
    <attachment name="paper.pdf" path="paper.pdf" type="file" />
  </attachments>
</submission>
"""

ITEM_XML = """
<response code="OK">
  <item id="assign12">
    <data>
      <type>Assignment</type>
      <title>Assignment 12</title>
      <abbreviation>A12</abbreviation>
      <perfectscore>10</perfectscore>
      <duedate>2025-09-01T23:59:00Z</duedate>
      <dropbox2 type="2" multiple="true" filetypes=".pdf" />
    </data>
  </item>
</response>
"""

ITEM_LIST_XML = """
<response code="OK">
  <items>
    <item id="assign12">
      <data>
        <type>Assignment</type>
        <title>Assignment 12</title>
        <abbreviation>A12</abbreviation>
        <perfectscore>10</perfectscore>
        <duedate>2025-09-01T23:59:00Z</duedate>
        <dropbox2 type="2" multiple="true" filetypes=".pdf" />
      </data>
    </item>
    <item id="lesson1">
      <data>
        <type>Lesson</type>
        <title>Lesson 1</title>
        <abbreviation>L1</abbreviation>
      </data>
    </item>
  </items>
</response>
"""

MANIFEST_XML = """
<response code="OK">
  <manifest schema="2" version="4378:15|4378:543" resourceentityid="4378,0">
    <item id="DEFAULT">
      <data>
        <parent>[-MANIFEST-]</parent>
        <title>Mathematics</title>
      </data>
      <item id="assign12">
        <data>
          <type>Assignment</type>
          <parent>DEFAULT</parent>
          <sequence>a</sequence>
          <title>Assignment 12</title>
          <abbreviation>A12</abbreviation>
          <href>Assets/assignment12.htm</href>
        </data>
      </item>
    </item>
  </manifest>
</response>
"""

COURSE_XML = """
<response code="OK">
  <course
    id="4378"
    title="Algebra I"
    domainid="100"
    reference="ALG-1"
    type="Course"
    startdate="2025-08-01T00:00:00Z"
    enddate="2026-05-30T00:00:00Z"
    version="12" />
</response>
"""

COURSES_XML = """
<response code="OK">
  <courses>
    <course id="4378" title="Algebra I" domainid="100" reference="ALG-1" type="Course" version="12" />
    <course id="4379" title="Geometry" domainid="100" reference="GEO" type="Continuous" version="3" />
  </courses>
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
    email="sally.johnson@example.edu"
    version="7" />
</response>
"""

ENROLLMENT_XML = """
<response code="OK">
  <enrollment
    id="4317"
    userid="9001"
    courseid="4378"
    privileges="Student"
    status="1"
    firstactivitydate="2025-08-10T12:00:00Z"
    lastactivitydate="2025-09-01T12:00:00Z" />
</response>
"""

ENROLLMENTS_XML = """
<response code="OK">
  <enrollments>
    <enrollment id="4317" userid="9001" courseid="4378" privileges="Student" status="1" />
    <enrollment id="4318" userid="9002" courseid="4378" privileges="Teacher" status="1" />
  </enrollments>
</response>
"""

QUESTION_XML = """
<response code="OK">
  <question questionid="q-choice">
    <body>Pick one.</body>
    <interaction type="choice">
      <choice id="1"><body>No</body></choice>
      <choice id="2"><body>Yes</body></choice>
    </interaction>
  </question>
</response>
"""


class FakeClient:
    base_url = "https://api.agilixbuzz.com"

    def __init__(self, *, fail_get_item: bool = False) -> None:
        self.fail_get_item = fail_get_item
        self.closed = False
        self.calls: list[str] = []

    def close(self) -> None:
        self.closed = True

    def get_student_submission(self, *, enrollmentid: str, itemid: str) -> str:
        self.calls.append(f"get_student_submission:{enrollmentid}:{itemid}")
        return SUBMISSION_XML

    def get_item(self, *, entityid: str, itemid: str) -> str:
        self.calls.append(f"get_item:{entityid}:{itemid}")
        if self.fail_get_item:
            raise BuzzApiError("GetItem failed")
        return ITEM_XML

    def get_item_list(self, *, entityid: str, itemid: str | None = None) -> str:
        self.calls.append(f"get_item_list:{entityid}:{itemid}")
        return ITEM_XML if itemid else ITEM_LIST_XML

    def get_manifest(self, *, entityid: str) -> str:
        self.calls.append(f"get_manifest:{entityid}")
        return MANIFEST_XML

    def get_course(self, *, courseid: str, version: str | None = None) -> str:
        self.calls.append(f"get_course:{courseid}:{version}")
        return COURSE_XML

    def list_courses(
        self,
        *,
        domainid: str,
        includedescendantdomains: bool = False,
        show: str = "current",
        text: str | None = None,
        limit: int = 50,
    ) -> str:
        self.calls.append(
            "list_courses:"
            f"{domainid}:{includedescendantdomains}:{show}:{text}:{limit}"
        )
        return COURSES_XML

    def get_user(self, *, userid: str) -> str:
        self.calls.append(f"get_user:{userid}")
        return USER_XML

    def get_enrollment(self, *, enrollmentid: str) -> str:
        self.calls.append(f"get_enrollment:{enrollmentid}")
        return ENROLLMENT_XML

    def list_user_enrollments(
        self,
        *,
        userid: str,
        entityid: str | None = None,
        allstatus: bool = False,
    ) -> str:
        self.calls.append(f"list_user_enrollments:{userid}:{entityid}:{allstatus}")
        return ENROLLMENTS_XML

    def list_entity_enrollments(
        self,
        *,
        entityid: str,
        userid: str | None = None,
        allstatus: bool = False,
    ) -> str:
        self.calls.append(f"list_entity_enrollments:{entityid}:{userid}:{allstatus}")
        return ENROLLMENTS_XML

    def list_questions(
        self,
        *,
        entityid: str,
        questionids: list[str] | None = None,
        itemid: str | None = None,
    ) -> str:
        self.calls.append(f"list_questions:{entityid}:{questionids}")
        return QUESTION_XML

    def get_question_list(self, *, entityid: str, questionids: list[str]) -> str:
        self.calls.append(f"get_question_list:{entityid}:{questionids}")
        return QUESTION_XML

    def submission_file_url(
        self, *, enrollmentid: str, itemid: str, filepath: str, inline: bool = True
    ) -> str:
        return f"https://download/submission/{enrollmentid}/{itemid}/{filepath}"

    def attempt_file_url(
        self,
        *,
        enrollmentid: str,
        itemid: str,
        partid: str,
        filepath: str,
        inline: bool = True,
    ) -> str:
        return f"https://download/attempt/{enrollmentid}/{itemid}/{partid}/{filepath}"


class BuzzReadServiceTests(unittest.TestCase):
    def test_get_activity_returns_normalized_activity_contract(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        activity = service.get_activity(entityid="4378", itemid="assign12")

        self.assertTrue(client.closed)
        self.assertEqual(activity["entityid"], "4378")
        self.assertEqual(activity["id"], "assign12")
        self.assertEqual(activity["title"], "Assignment 12")
        self.assertTrue(activity["accepts_file_upload"])
        self.assertEqual(activity["allowed_filetypes"], ".pdf")

    def test_get_activity_falls_back_to_item_list(self) -> None:
        client = FakeClient(fail_get_item=True)
        service = BuzzReadService(lambda: client)

        activity = service.get_activity(entityid="4378", itemid="assign12")

        self.assertEqual(activity["title"], "Assignment 12")
        self.assertIn("get_item_list:4378:assign12", client.calls)

    def test_get_activity_does_not_fallback_on_auth_error(self) -> None:
        class AuthFailClient(FakeClient):
            def get_item(self, *, entityid: str, itemid: str) -> str:
                self.calls.append(f"get_item:{entityid}:{itemid}")
                raise BuzzApiError("auth failed", code="AUTH_REQUIRED")

        client = AuthFailClient()
        service = BuzzReadService(lambda: client)

        with self.assertRaises(BuzzApiError) as raised:
            service.get_activity(entityid="4378", itemid="assign12")

        self.assertEqual(raised.exception.code, "AUTH_REQUIRED")
        self.assertNotIn("get_item_list:4378:assign12", client.calls)

    def test_list_activities_returns_normalized_manifest(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        manifest = service.list_activities(entityid="4378")

        self.assertTrue(client.closed)
        self.assertEqual(manifest["entityid"], "4378")
        self.assertEqual(manifest["count"], 2)
        activities = manifest["activities"]
        self.assertEqual(
            [activity["id"] for activity in activities],
            ["assign12", "lesson1"],
        )
        self.assertEqual(activities[0]["entityid"], "4378")
        self.assertTrue(activities[0]["accepts_file_upload"])
        self.assertFalse(activities[1]["accepts_file_upload"])
        self.assertIn("get_item_list:4378:None", client.calls)

    def test_get_manifest_returns_bounded_content_tree_summary(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        manifest = service.get_manifest(entityid="4378", limit=1)

        self.assertTrue(client.closed)
        self.assertEqual(manifest["entityid"], "4378")
        self.assertEqual(manifest["version"], "4378:15|4378:543")
        self.assertEqual(manifest["count"], 1)
        self.assertEqual(manifest["total_count"], 2)
        self.assertTrue(manifest["truncated"])
        self.assertEqual(manifest["items"][0]["id"], "DEFAULT")
        self.assertIn("get_manifest:4378", client.calls)

    def test_get_manifest_validates_limit(self) -> None:
        service = BuzzReadService(FakeClient)

        with self.assertRaises(BuzzApiError) as raised:
            service.get_manifest(entityid="4378", limit=501)

        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(raised.exception.details["field"], "limit")

    def test_get_course_returns_normalized_course(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        course = service.get_course(courseid="4378", version="12")

        self.assertTrue(client.closed)
        self.assertEqual(course["entityid"], "4378")
        self.assertEqual(course["title"], "Algebra I")
        self.assertEqual(course["type"], "Course")
        self.assertIn("get_course:4378:12", client.calls)

    def test_list_courses_returns_limited_contract(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        payload = service.list_courses(
            domainid="100",
            includedescendantdomains=True,
            show="active",
            text="Algebra",
            limit=1,
        )

        self.assertTrue(client.closed)
        self.assertEqual(payload["domainid"], "100")
        self.assertTrue(payload["includedescendantdomains"])
        self.assertEqual(payload["show"], "active")
        self.assertEqual(payload["text"], "Algebra")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(payload["courses"][0]["entityid"], "4378")
        self.assertIn("list_courses:100:True:active:Algebra:1", client.calls)

    def test_list_courses_rejects_domain_zero(self) -> None:
        service = BuzzReadService(FakeClient)

        with self.assertRaises(BuzzApiError) as raised:
            service.list_courses(domainid="0")

        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(raised.exception.details["field"], "domainid")

    def test_list_courses_rejects_deleted_or_all_scope(self) -> None:
        service = BuzzReadService(FakeClient)

        with self.assertRaises(BuzzApiError) as raised:
            service.list_courses(domainid="100", show="all")  # type: ignore[arg-type]

        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(raised.exception.details["field"], "show")

    def test_get_user_returns_privacy_redacted_user(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        user = service.get_user(userid="9001")

        self.assertTrue(client.closed)
        self.assertEqual(user["id"], "9001")
        self.assertEqual(user["display_name"], "Sally Johnson")
        self.assertEqual(user["reference"], "student-ref")
        self.assertTrue(user["pii_redacted"])
        self.assertNotIn("email", user)
        self.assertIn("get_user:9001", client.calls)

    def test_get_enrollment_returns_normalized_enrollment(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        enrollment = service.get_enrollment(enrollmentid="4317")

        self.assertTrue(client.closed)
        self.assertEqual(enrollment["enrollmentid"], "4317")
        self.assertEqual(enrollment["entityid"], "4378")
        self.assertEqual(enrollment["userid"], "9001")
        self.assertEqual(enrollment["role"], "Student")

    def test_list_user_enrollments_returns_limited_contract(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        payload = service.list_user_enrollments(
            userid="9001",
            entityid="4378",
            allstatus=True,
            limit=1,
        )

        self.assertTrue(client.closed)
        self.assertEqual(payload["userid"], "9001")
        self.assertEqual(payload["entityid"], "4378")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(payload["enrollments"][0]["enrollmentid"], "4317")
        self.assertIn("list_user_enrollments:9001:4378:True", client.calls)

    def test_list_entity_enrollments_returns_normalized_contract(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        payload = service.list_entity_enrollments(entityid="4378", userid="9001")

        self.assertTrue(client.closed)
        self.assertEqual(payload["entityid"], "4378")
        self.assertEqual(payload["userid"], "9001")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(
            [enrollment["enrollmentid"] for enrollment in payload["enrollments"]],
            ["4317", "4318"],
        )

    def test_list_enrollments_validates_limit(self) -> None:
        service = BuzzReadService(FakeClient)

        with self.assertRaises(BuzzApiError) as raised:
            service.list_entity_enrollments(entityid="4378", limit=101)

        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(raised.exception.details["field"], "limit")

    def test_get_submission_report_uses_buzz_workflow_and_url_builder(self) -> None:
        client = FakeClient()
        service = BuzzReadService(lambda: client)

        report = service.get_submission_report(
            enrollmentid="4317", itemid="assign12", entityid="4378"
        )

        self.assertTrue(client.closed)
        self.assertEqual(report["activity_title"], "Assignment 12")
        self.assertEqual(report["q_and_a_pairs"][0]["answer"], "Yes")
        self.assertEqual(len(report["student_attachments"]), 1)
        self.assertEqual(
            report["student_attachments"][0]["download_url"],
            "https://download/submission/4317/assign12/paper.pdf",
        )

    def test_get_attachment_url_validates_attempt_partid(self) -> None:
        service = BuzzReadService(FakeClient)

        with self.assertRaisesRegex(BuzzApiError, "partid is required") as raised:
            service.get_attachment_url(
                enrollmentid="4317",
                itemid="assign12",
                filepath="paper.pdf",
                source="attempt-question",
            )
        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(raised.exception.details, {"field": "partid"})

    def test_get_attachment_url_returns_attempt_url(self) -> None:
        service = BuzzReadService(FakeClient)

        payload = service.get_attachment_url(
            enrollmentid="4317",
            itemid="assign12",
            filepath="paper.pdf",
            source="attempt-question",
            partid="5",
        )

        self.assertEqual(payload["source"], "attempt-question")
        self.assertEqual(payload["partid"], "5")
        self.assertEqual(
            payload["download_url"],
            "https://download/attempt/4317/assign12/5/paper.pdf",
        )


if __name__ == "__main__":
    unittest.main()
