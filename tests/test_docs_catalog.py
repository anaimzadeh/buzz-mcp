from __future__ import annotations

import unittest

from buzz_submission_mcp.buzz_client import BuzzApiError
from buzz_submission_mcp.docs_catalog import (
    DOC_ENTRIES,
    get_command_entry,
    get_schema_entry,
    search_docs,
)


class DocsCatalogTests(unittest.TestCase):
    def test_catalog_contains_current_submission_review_commands(self) -> None:
        commands = {
            entry.name
            for entry in DOC_ENTRIES
            if entry.entry_type == "command" and entry.mcp_phase == "current PoC"
        }

        self.assertIn("GetStudentSubmission", commands)
        self.assertIn("GetItem", commands)
        self.assertIn("GetItemList", commands)
        self.assertIn("ListQuestions", commands)
        self.assertIn("GetAttemptFile", commands)

    def test_catalog_contains_core_entity_graph_commands(self) -> None:
        commands = {
            entry.name
            for entry in DOC_ENTRIES
            if entry.entry_type == "command" and entry.mcp_phase == "core entity graph"
        }

        self.assertIn("GetCourse2", commands)
        self.assertIn("ListCourses", commands)
        self.assertIn("GetUser2", commands)
        self.assertIn("GetEnrollment3", commands)
        self.assertIn("ListUserEnrollments", commands)
        self.assertIn("ListEntityEnrollments", commands)

    def test_search_docs_finds_relevant_command_without_credentials(self) -> None:
        results = search_docs(query="student submission", entry_type="command", limit=5)

        self.assertEqual(results["query"], "student submission")
        self.assertGreaterEqual(results["count"], 1)
        names = [entry["name"] for entry in results["results"]]
        self.assertIn("GetStudentSubmission", names)

    def test_search_docs_can_filter_schemas(self) -> None:
        results = search_docs(query="gradebook rollups", entry_type="schema", limit=5)

        self.assertEqual(results["count"], 1)
        self.assertEqual(results["results"][0]["name"], "Grades")
        self.assertEqual(results["results"][0]["entry_type"], "schema")

    def test_get_command_entry_normalizes_command_name(self) -> None:
        command = get_command_entry("get-student-submission")

        self.assertEqual(command["name"], "GetStudentSubmission")
        self.assertEqual(command["path"], "Command/GetStudentSubmission")
        self.assertTrue(command["sensitive"])
        self.assertIn("Submission", command["related"])

    def test_get_schema_entry_returns_schema_metadata(self) -> None:
        schema = get_schema_entry("submission")

        self.assertEqual(schema["name"], "Submission")
        self.assertEqual(
            schema["source_url"],
            "https://api.agilixbuzz.com/docs/entry/Schema/Submission",
        )
        self.assertTrue(schema["sensitive"])

    def test_unknown_command_has_stable_error(self) -> None:
        with self.assertRaises(BuzzApiError) as raised:
            get_command_entry("DeleteEverything")

        self.assertEqual(raised.exception.code, "INVALID_ID")
        self.assertEqual(
            raised.exception.details,
            {"entry_type": "command", "name": "DeleteEverything"},
        )

    def test_search_validates_entry_type_and_limit(self) -> None:
        with self.assertRaises(BuzzApiError) as entry_type_error:
            search_docs(query="course", entry_type="bad", limit=10)  # type: ignore[arg-type]
        self.assertEqual(entry_type_error.exception.details["field"], "entry_type")

        with self.assertRaises(BuzzApiError) as limit_error:
            search_docs(query="course", limit=0)
        self.assertEqual(limit_error.exception.details["field"], "limit")


if __name__ == "__main__":
    unittest.main()
