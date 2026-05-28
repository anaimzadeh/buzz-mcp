from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.reporting import (
    SubmissionRequest,
    build_complete_submission_report,
    extract_item_info,
    extract_item_infos,
    extract_question_ids,
    extract_questions,
    flatten_submission_answers,
    normalize_submission_request,
)


SUBMISSION_XML = """
<submission type="attempt">
  <submission type="attempt" partid="attempt-1">
    <submission type="question">
      <attemptquestion questionid="q-choice" />
      <answer>2</answer>
    </submission>
    <submission type="group" partid="nested">
      <submission type="question">
        <attemptquestion id="q-essay" />
        <notes><![CDATA[My <b>essay</b> answer]]></notes>
      </submission>
      <submission type="question" partid="5">
        <attemptquestion questionid="q-file" />
        <attachments>
          <attachment name="paper.pdf" path="paper.pdf" />
        </attachments>
      </submission>
    </submission>
  </submission>
</submission>
"""

ITEM_XML = """
<response code="OK">
  <items>
    <item id="assign12">
      <data>
        <type>Assignment</type>
        <title>Assignment 12</title>
        <abbreviation>A12</abbreviation>
        <perfectscore>10</perfectscore>
        <duedate>2025-09-01T23:59:00Z</duedate>
        <dropbox2 version="1" type="2" multiple="true" filetypes=".pdf,.docx" />
      </data>
    </item>
  </items>
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
        <dropbox2 version="1" type="2" multiple="true" filetypes=".pdf,.docx" />
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

QUESTION_XML = """
<response code="OK">
  <responses>
    <response code="OK">
      <question questionid="q-choice">
        <body>Pick one.</body>
        <interaction type="choice">
          <choice id="1"><body>No</body></choice>
          <choice id="2"><body>Yes</body></choice>
        </interaction>
      </question>
      <question questionid="q-essay">
        <body>Explain the idea.</body>
        <interaction type="essay" />
      </question>
      <question questionid="q-file">
        <body>Upload your work.</body>
        <interaction type="fileupload" />
      </question>
    </response>
  </responses>
</response>
"""


REQUEST = SubmissionRequest(enrollmentid="4317", itemid="assign12", entityid="4378")


class ReportingTests(unittest.TestCase):
    def test_flatten_submission_answers_recurses_through_nested_submissions(self) -> None:
        answers = flatten_submission_answers(SUBMISSION_XML)

        self.assertEqual(
            [answer.questionid for answer in answers],
            ["q-choice", "q-essay", "q-file"],
        )
        self.assertEqual(answers[1].answer, "My essay answer")
        # Attachment-only question carries an empty answer string with attachments populated.
        self.assertEqual(answers[2].answer, "")
        self.assertEqual(len(answers[2].attachments), 1)
        self.assertEqual(answers[2].attachments[0].name, "paper.pdf")
        self.assertEqual(answers[2].partid, "5")

    def test_extract_question_ids_preserves_order_and_uniqueness(self) -> None:
        self.assertEqual(extract_question_ids(SUBMISSION_XML), ["q-choice", "q-essay", "q-file"])

    def test_extract_item_info_returns_full_metadata_for_assignment(self) -> None:
        info = extract_item_info(ITEM_XML)

        self.assertEqual(info.itemid, "assign12")
        self.assertEqual(info.title, "Assignment 12")
        self.assertEqual(info.item_type, "Assignment")
        self.assertEqual(info.abbreviation, "A12")
        self.assertTrue(info.accepts_file_upload)
        self.assertEqual(info.allowed_filetypes, ".pdf,.docx")
        self.assertTrue(info.dropbox_multiple)
        self.assertEqual(info.perfect_score, "10")
        self.assertTrue(info.is_assignment)

    def test_extract_item_infos_returns_all_items_in_order(self) -> None:
        infos = extract_item_infos(ITEM_LIST_XML)

        self.assertEqual([info.itemid for info in infos], ["assign12", "lesson1"])
        self.assertEqual([info.title for info in infos], ["Assignment 12", "Lesson 1"])
        self.assertTrue(infos[0].accepts_file_upload)
        self.assertFalse(infos[1].accepts_file_upload)

    def test_extract_item_info_recognizes_custom_activity_without_dropbox(self) -> None:
        xml = """
        <response code="OK">
          <item id="ca-1">
            <data>
              <type>CustomActivity</type>
              <title>SCO Lesson 1</title>
            </data>
          </item>
        </response>
        """

        info = extract_item_info(xml)

        self.assertTrue(info.is_custom_activity)
        self.assertFalse(info.accepts_file_upload)
        self.assertEqual(info.allowed_filetypes, "")

    def test_build_complete_submission_report_maps_choice_ids_and_builds_attachment_url(self) -> None:
        report = build_complete_submission_report(
            submission_xml=SUBMISSION_XML,
            item_xml=ITEM_XML,
            question_xml=QUESTION_XML,
            base_url="https://api.agilixbuzz.com",
            request=REQUEST,
        )

        self.assertEqual(report["activity_title"], "Assignment 12")
        self.assertEqual(report["activity"]["type"], "Assignment")
        self.assertTrue(report["activity"]["accepts_file_upload"])

        # No top-level attachments on this submission.
        self.assertEqual(report["student_attachments"], [])

        pairs = report["q_and_a_pairs"]
        self.assertEqual(pairs[0]["question"], "Pick one.")
        self.assertEqual(pairs[0]["answer"], "Yes")
        self.assertEqual(pairs[0]["interaction_type"], "choice")

        self.assertEqual(pairs[1]["answer"], "My essay answer")

        # Fileupload question got an attempt-file URL keyed by partid.
        self.assertEqual(pairs[2]["question"], "Upload your work.")
        self.assertEqual(pairs[2]["interaction_type"], "fileupload")
        attachments = pairs[2]["attachments"]
        self.assertEqual(len(attachments), 1)
        url = attachments[0]["download_url"]
        self.assertIn("cmd=getattemptfile", url)
        self.assertIn("enrollmentid=4317", url)
        self.assertIn("partid=5", url)
        self.assertIn("filepath=paper.pdf", url)
        # The humanized answer surfaces the download URL too.
        self.assertEqual(pairs[2]["answer"], url)

    def test_top_level_submission_attachments_get_submission_file_url(self) -> None:
        submission_xml = """
        <submission type="assignment">
          <attachments>
            <attachment name="MyPaper.pdf" path="MyPaper.pdf" type="file" />
            <attachment name="Doc" path="https://drive.google.com/abc" type="googledrivedoc" />
          </attachments>
        </submission>
        """
        item_xml = ITEM_XML
        question_xml = "<response code=\"OK\"></response>"

        report = build_complete_submission_report(
            submission_xml=submission_xml,
            item_xml=item_xml,
            question_xml=question_xml,
            base_url="https://api.agilixbuzz.com",
            request=REQUEST,
        )

        attachments = report["student_attachments"]
        self.assertEqual(len(attachments), 2)
        url = attachments[0]["download_url"]
        self.assertIn("cmd=getstudentsubmission", url)
        self.assertIn("packagetype=file", url)
        self.assertIn("itemid=assign12", url)
        self.assertIn("filepath=MyPaper.pdf", url)
        # Google Drive attachments pass through their own URL unchanged.
        self.assertEqual(attachments[1]["download_url"], "https://drive.google.com/abc")

    def test_humanize_multiple_answer_and_order_and_match(self) -> None:
        submission_xml = """
        <submission type="attempt">
          <submission type="question">
            <attemptquestion questionid="q-multi" />
            <answer>1,3</answer>
          </submission>
          <submission type="question">
            <attemptquestion questionid="q-order" />
            <answer>2,1,3</answer>
          </submission>
          <submission type="question">
            <attemptquestion questionid="q-match" />
            <answer>woof,meow,moo</answer>
          </submission>
        </submission>
        """
        question_xml = """
        <response code="OK">
          <question questionid="q-multi">
            <body>Select all true statements.</body>
            <interaction type="answer">
              <choice id="1"><body>Sky is blue</body></choice>
              <choice id="2"><body>Grass is purple</body></choice>
              <choice id="3"><body>Water is wet</body></choice>
            </interaction>
          </question>
          <question questionid="q-order">
            <body>Order these.</body>
            <interaction type="order">
              <choice id="1"><body>First</body></choice>
              <choice id="2"><body>Zero</body></choice>
              <choice id="3"><body>Second</body></choice>
            </interaction>
          </question>
          <question questionid="q-match">
            <body>Match the animal sounds.</body>
            <interaction type="match">
              <choice id="1"><body>dog</body><answer>woof</answer></choice>
              <choice id="2"><body>cat</body><answer>meow</answer></choice>
              <choice id="3"><body>cow</body><answer>moo</answer></choice>
            </interaction>
          </question>
        </response>
        """

        report = build_complete_submission_report(
            submission_xml=submission_xml,
            item_xml=ITEM_XML,
            question_xml=question_xml,
            base_url="https://api.agilixbuzz.com",
            request=REQUEST,
        )
        pairs = report["q_and_a_pairs"]

        self.assertEqual(pairs[0]["answer"], "Sky is blue, Water is wet")
        self.assertEqual(pairs[1]["answer"], "Zero → First → Second")
        self.assertEqual(
            pairs[2]["answer"], "dog → woof, cat → meow, cow → moo"
        )

    def test_extract_questions_returns_empty_for_no_question_payload(self) -> None:
        self.assertEqual(extract_questions("<response code=\"OK\"></response>"), {})

    def test_normalize_submission_request_accepts_json_submissionid(self) -> None:
        request = normalize_submission_request(
            submissionid='{"enrollmentid":"4317","itemid":"assign12","entityid":"4378"}'
        )

        self.assertEqual(request.enrollmentid, "4317")
        self.assertEqual(request.itemid, "assign12")
        self.assertEqual(request.entityid, "4378")

    def test_normalize_submission_request_explains_missing_real_buzz_ids(self) -> None:
        with self.assertRaisesRegex(
            BuzzApiError, "GetStudentSubmission uses enrollmentid and itemid"
        ) as raised:
            normalize_submission_request(submissionid="single-id")
        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(
            raised.exception.details,
            {"missing_ids": ["enrollmentid", "itemid", "entityid"]},
        )

    def test_bad_submissionid_json_is_invalid_id(self) -> None:
        with self.assertRaisesRegex(BuzzApiError, "looked like JSON") as raised:
            normalize_submission_request(submissionid="{not json")
        self.assertEqual(raised.exception.code, "INVALID_ID")


if __name__ == "__main__":
    unittest.main()
