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
        return ITEM_XML

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

        with self.assertRaisesRegex(BuzzApiError, "partid is required"):
            service.get_attachment_url(
                enrollmentid="4317",
                itemid="assign12",
                filepath="paper.pdf",
                source="attempt-question",
            )

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
