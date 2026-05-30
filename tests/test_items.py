from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.items import extract_item_list, extract_item_summary


ITEM_XML = """
<response code="OK">
  <item
      id="DISCUSSION_1__POINTS"
      resourceentityid="20723"
      creationdate="2009-10-30T22:01:58.887Z"
      modifieddate="2009-11-05T00:20:34.96Z"
      version="3"
      origindepth="1"
      derivativedepth="2">
    <data>
      <type>Discussion</type>
      <parent>MODULE 1</parent>
      <sequence>f</sequence>
      <title>Discussion #1 - Points</title>
      <abbreviation>D#1- P</abbreviation>
      <folder>XLBSJ</folder>
      <href>Templates/Data/XLBSJ/index.html</href>
      <period>0</period>
      <category>4</category>
      <duedate>2010-08-25T23:59:00Z</duedate>
      <availabledate>2010-08-01T00:00:00Z</availabledate>
      <allowlatesubmission_>true</allowlatesubmission_>
      <gradable_>true</gradable_>
      <perfectscore_>1</perfectscore_>
      <weight_>50</weight_>
      <dropbox2 type="6" multiple="true" filetypes="pdf|docx" />
    </data>
  </item>
</response>
"""

ITEM_LIST_XML = """
<response code="OK">
  <items>
    <item id="Assignment12" version="3">
      <data>
        <type>Assignment</type>
        <parent>DEFAULT</parent>
        <sequence>a</sequence>
        <title>Assignment 12</title>
        <href>Assets/assignment12.htm</href>
        <gradable>true</gradable>
      </data>
    </item>
    <item id="Lesson1">
      <data>
        <type>Lesson</type>
        <parent>DEFAULT</parent>
        <sequence>b</sequence>
        <title>Lesson 1</title>
        <href>Assets/lesson1.htm</href>
      </data>
    </item>
  </items>
</response>
"""


class ItemParserTests(unittest.TestCase):
    def test_extract_item_summary_returns_normalized_metadata(self) -> None:
        item = extract_item_summary(
            ITEM_XML,
            entityid="4378",
            requested_itemid="DISCUSSION_1__POINTS",
        )

        self.assertEqual(item["entityid"], "4378")
        self.assertEqual(item["id"], "DISCUSSION_1__POINTS")
        self.assertEqual(item["title"], "Discussion #1 - Points")
        self.assertEqual(item["type"], "Discussion")
        self.assertEqual(item["parentid"], "MODULE 1")
        self.assertEqual(item["sequence"], "f")
        self.assertEqual(item["href"], "Templates/Data/XLBSJ/index.html")
        self.assertEqual(item["folder"], "XLBSJ")
        self.assertEqual(item["category"], "4")
        self.assertEqual(item["period"], "0")
        self.assertEqual(item["resourceentityid"], "20723")
        self.assertEqual(item["creation_date"], "2009-10-30T22:01:58.887Z")
        self.assertEqual(item["modified_date"], "2009-11-05T00:20:34.96Z")
        self.assertEqual(item["version"], "3")
        self.assertEqual(item["origin_depth"], "1")
        self.assertEqual(item["derivative_depth"], "2")
        self.assertEqual(item["due_date"], "2010-08-25T23:59:00Z")
        self.assertEqual(item["available_date"], "2010-08-01T00:00:00Z")
        self.assertTrue(item["gradable"])
        self.assertTrue(item["allow_late_submission"])
        self.assertEqual(item["perfect_score"], "1")
        self.assertEqual(item["weight"], "50")
        self.assertTrue(item["accepts_file_upload"])
        self.assertEqual(item["allowed_filetypes"], "pdf|docx")
        self.assertTrue(item["dropbox_multiple"])

    def test_extract_item_summary_uses_requested_id_as_fallback(self) -> None:
        xml = """
        <response code="OK">
          <item>
            <data>
              <title>Untyped Item</title>
            </data>
          </item>
        </response>
        """

        item = extract_item_summary(xml, entityid="4378", requested_itemid="fallback")

        self.assertEqual(item["id"], "fallback")
        self.assertEqual(item["title"], "Untyped Item")
        self.assertEqual(item["type"], "")
        self.assertFalse(item["gradable"])

    def test_extract_item_list_returns_bounded_items(self) -> None:
        payload = extract_item_list(ITEM_LIST_XML, entityid="4378", limit=1)

        self.assertEqual(payload["entityid"], "4378")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["total_count"], 2)
        self.assertEqual(payload["limit"], 1)
        self.assertTrue(payload["truncated"])
        self.assertEqual(payload["items"][0]["id"], "Assignment12")
        self.assertEqual(payload["items"][0]["version"], "3")
        self.assertTrue(payload["items"][0]["gradable"])

    def test_extract_item_list_allows_empty_results(self) -> None:
        payload = extract_item_list(
            '<response code="OK"><items /></response>',
            entityid="4378",
            limit=10,
        )

        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["total_count"], 0)
        self.assertFalse(payload["truncated"])

    def test_extract_item_summary_requires_item_node(self) -> None:
        with self.assertRaises(BuzzApiError) as raised:
            extract_item_summary(
                '<response code="OK" />',
                entityid="4378",
                requested_itemid="x",
            )

        self.assertEqual(raised.exception.code, "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
