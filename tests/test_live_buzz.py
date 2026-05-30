from __future__ import annotations

import os
import unittest

from buzz_submission_mcp.service import BuzzReadService


REQUIRED_LIVE_ENV = (
    "BUZZ_USERNAME",
    "BUZZ_PASSWORD",
    "BUZZ_DOMAIN",
    "BUZZ_TEST_ENTITYID",
    "BUZZ_TEST_ITEMID",
    "BUZZ_TEST_ENROLLMENTID",
)


def _missing_live_env() -> list[str]:
    missing: list[str] = []
    if os.getenv("BUZZ_RUN_LIVE_TESTS") != "1":
        missing.append("BUZZ_RUN_LIVE_TESTS=1")
    missing.extend(key for key in REQUIRED_LIVE_ENV if not os.getenv(key))
    return missing


LIVE_SKIP_REASON = "Live Buzz sandbox tests disabled; missing " + ", ".join(
    _missing_live_env()
)


@unittest.skipIf(_missing_live_env(), LIVE_SKIP_REASON)
class LiveBuzzSandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entityid = os.environ["BUZZ_TEST_ENTITYID"]
        self.itemid = os.environ["BUZZ_TEST_ITEMID"]
        self.enrollmentid = os.environ["BUZZ_TEST_ENROLLMENTID"]
        self.service = BuzzReadService()

    def test_live_get_activity_contract(self) -> None:
        activity = self.service.get_activity(
            entityid=self.entityid,
            itemid=self.itemid,
        )

        self.assertEqual(activity["id"], self.itemid)
        self.assertEqual(activity["entityid"], self.entityid)
        self.assertIsInstance(activity["title"], str)
        self.assertIn("accepts_file_upload", activity)
        self.assertIn("due_date", activity)

    def test_live_list_activities_contract(self) -> None:
        manifest = self.service.list_activities(entityid=self.entityid)

        self.assertEqual(manifest["entityid"], self.entityid)
        self.assertGreaterEqual(manifest["count"], 1)
        self.assertIsInstance(manifest["activities"], list)
        self.assertEqual(manifest["count"], len(manifest["activities"]))
        self.assertIn(
            self.itemid,
            {activity["id"] for activity in manifest["activities"]},
        )

    def test_live_get_course_contract(self) -> None:
        course = self.service.get_course(courseid=self.entityid)

        self.assertEqual(course["entityid"], self.entityid)
        self.assertIsInstance(course["title"], str)
        self.assertTrue(course["title"])
        self.assertIn("type", course)

    @unittest.skipUnless(
        os.getenv("BUZZ_TEST_DOMAINID"),
        "BUZZ_TEST_DOMAINID not set",
    )
    def test_live_list_courses_contract(self) -> None:
        payload = self.service.list_courses(
            domainid=os.environ["BUZZ_TEST_DOMAINID"],
            text=self.entityid,
            limit=5,
        )

        self.assertEqual(payload["domainid"], os.environ["BUZZ_TEST_DOMAINID"])
        self.assertLessEqual(payload["count"], 5)
        self.assertIsInstance(payload["courses"], list)
        for course in payload["courses"]:
            self.assertIn("entityid", course)
            self.assertIn("title", course)

    def test_live_get_enrollment_contract(self) -> None:
        enrollment = self.service.get_enrollment(enrollmentid=self.enrollmentid)

        self.assertEqual(enrollment["enrollmentid"], self.enrollmentid)
        self.assertEqual(enrollment["entityid"], self.entityid)
        self.assertIsInstance(enrollment["userid"], str)
        self.assertIn("status", enrollment)

    @unittest.skipUnless(
        os.getenv("BUZZ_TEST_USERID"),
        "BUZZ_TEST_USERID not set",
    )
    def test_live_get_user_contract(self) -> None:
        user = self.service.get_user(userid=os.environ["BUZZ_TEST_USERID"])

        self.assertEqual(user["id"], os.environ["BUZZ_TEST_USERID"])
        self.assertIsInstance(user["display_name"], str)
        self.assertIn("reference", user)
        self.assertTrue(user["pii_redacted"])
        self.assertNotIn("email", user)

    def test_live_get_submission_report_contract(self) -> None:
        report = self.service.get_submission_report(
            enrollmentid=self.enrollmentid,
            itemid=self.itemid,
            entityid=self.entityid,
        )

        self.assertEqual(report["activity"]["id"], self.itemid)
        self.assertEqual(report["activity_title"], report["activity"]["title"])
        self.assertIsInstance(report["student_attachments"], list)
        self.assertIsInstance(report["q_and_a_pairs"], list)
        for pair in report["q_and_a_pairs"]:
            self.assertIn("question", pair)
            self.assertIn("answer", pair)

    @unittest.skipUnless(
        os.getenv("BUZZ_TEST_ATTACHMENT_FILEPATH"),
        "BUZZ_TEST_ATTACHMENT_FILEPATH not set",
    )
    def test_live_get_attachment_url_contract(self) -> None:
        payload = self.service.get_attachment_url(
            enrollmentid=self.enrollmentid,
            itemid=self.itemid,
            filepath=os.environ["BUZZ_TEST_ATTACHMENT_FILEPATH"],
            source="submission",
        )

        self.assertEqual(payload["source"], "submission")
        self.assertEqual(payload["filepath"], os.environ["BUZZ_TEST_ATTACHMENT_FILEPATH"])
        self.assertIn("cmd=getstudentsubmission", payload["download_url"])
        self.assertIn("_token=", payload["download_url"])


if __name__ == "__main__":
    unittest.main()
