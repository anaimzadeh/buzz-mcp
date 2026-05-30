from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.manifest import extract_manifest_summary


MANIFEST_XML = """
<response code="OK">
  <manifest schema="2" version="4378:15|4378:543" resourceentityid="4378,0">
    <data>
      <title>Course Data</title>
    </data>
    <item id="DEFAULT">
      <data>
        <parent>[-MANIFEST-]</parent>
        <title>Mathematics</title>
        <category>0</category>
      </data>
      <item id="Assignment1">
        <data>
          <type>Assignment</type>
          <parent>DEFAULT</parent>
          <sequence>a</sequence>
          <title>Assignment 1</title>
          <abbreviation>A1</abbreviation>
          <href>Assets/assignment1.htm</href>
        </data>
      </item>
      <item id="OR5TGN" partial="true" resourceentityid="4000">
        <data>
          <type>AssetLink</type>
          <parent>DEFAULT</parent>
          <sequence>b</sequence>
          <title>Count, Read and Write 1-100</title>
          <category>0</category>
          <href>Assets/reading.htm</href>
        </data>
      </item>
    </item>
  </manifest>
</response>
"""


class ManifestParserTests(unittest.TestCase):
    def test_extract_manifest_summary_returns_depth_first_items(self) -> None:
        manifest = extract_manifest_summary(MANIFEST_XML, entityid="4378", limit=10)

        self.assertEqual(manifest["entityid"], "4378")
        self.assertEqual(manifest["schema_version"], "2")
        self.assertEqual(manifest["version"], "4378:15|4378:543")
        self.assertEqual(manifest["resourceentityid"], "4378,0")
        self.assertEqual(manifest["count"], 3)
        self.assertEqual(manifest["total_count"], 3)
        self.assertFalse(manifest["truncated"])
        self.assertEqual(
            [item["id"] for item in manifest["items"]],
            ["DEFAULT", "Assignment1", "OR5TGN"],
        )
        self.assertEqual(manifest["items"][0]["type"], "Folder")
        self.assertEqual(manifest["items"][1]["depth"], 1)
        self.assertEqual(manifest["items"][1]["path"], ["DEFAULT", "Assignment1"])
        self.assertEqual(manifest["items"][1]["href"], "Assets/assignment1.htm")
        self.assertTrue(manifest["items"][2]["partial"])
        self.assertEqual(manifest["items"][2]["resourceentityid"], "4000")

    def test_extract_manifest_summary_reports_truncation(self) -> None:
        manifest = extract_manifest_summary(MANIFEST_XML, entityid="4378", limit=2)

        self.assertEqual(manifest["count"], 2)
        self.assertEqual(manifest["total_count"], 3)
        self.assertTrue(manifest["truncated"])

    def test_extract_manifest_summary_requires_manifest_node(self) -> None:
        with self.assertRaises(BuzzApiError) as raised:
            extract_manifest_summary('<response code="OK" />', entityid="4378", limit=10)

        self.assertEqual(raised.exception.code, "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
