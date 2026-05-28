from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import patch

import buzz_submission_mcp.server as server


ACTIVITY = {
    "id": "assign12",
    "entityid": "4378",
    "title": "Assignment 12",
    "type": "Assignment",
    "abbreviation": "A12",
    "accepts_file_upload": True,
    "allowed_filetypes": ".pdf",
    "dropbox_multiple": True,
    "perfect_score": "10",
    "due_date": "2025-09-01T23:59:00Z",
}

REPORT = {
    "activity_title": "Assignment 12",
    "activity": {key: value for key, value in ACTIVITY.items() if key != "entityid"},
    "student_attachments": [],
    "q_and_a_pairs": [{"question": "Pick one.", "answer": "Yes"}],
}


class FakeService:
    def get_activity(self, *, entityid: str, itemid: str) -> dict[str, object]:
        activity = dict(ACTIVITY)
        activity["entityid"] = entityid
        activity["id"] = itemid
        return activity

    def list_activities(self, *, entityid: str) -> dict[str, object]:
        activity = dict(ACTIVITY)
        activity["entityid"] = entityid
        lesson = {
            **ACTIVITY,
            "id": "lesson1",
            "entityid": entityid,
            "title": "Lesson 1",
            "type": "Lesson",
            "abbreviation": "L1",
            "accepts_file_upload": False,
            "allowed_filetypes": "",
            "dropbox_multiple": False,
            "perfect_score": "",
            "due_date": "",
        }
        return {"entityid": entityid, "count": 2, "activities": [activity, lesson]}

    def get_submission_report(self, **kwargs: object) -> dict[str, object]:
        return REPORT

    def get_attachment_url(self, **kwargs: object) -> dict[str, object]:
        return {
            "download_url": "https://download/submission/4317/assign12/paper.pdf",
            "source": kwargs["source"],
            "filepath": kwargs["filepath"],
        }


class ServerContractTests(unittest.TestCase):
    def test_server_registers_poc_tools_with_output_schemas(self) -> None:
        async def run() -> dict[str, object]:
            tools = await server.mcp.list_tools()
            return {tool.name: tool for tool in tools}

        tools = asyncio.run(run())

        for name in {
            "buzz.get_activity",
            "buzz.list_activities",
            "buzz.get_submission_report",
            "buzz.get_attachment_url",
            "get_complete_submission_report",
        }:
            self.assertIn(name, tools)
            self.assertTrue(tools[name].output_schema)
        self.assertEqual(
            tools["buzz.get_attachment_url"].parameters["properties"]["source"]["enum"],
            ["submission", "attempt-question"],
        )

    def test_server_registers_resource_templates(self) -> None:
        async def run() -> set[str]:
            templates = await server.mcp.list_resource_templates()
            return {template.uri_template for template in templates}

        templates = asyncio.run(run())

        self.assertIn("buzz://course/{entityid}/item/{itemid}", templates)
        self.assertIn("buzz://course/{entityid}/manifest", templates)
        self.assertIn(
            "buzz://submission/{enrollmentid}/{itemid}/report{?entityid}",
            templates,
        )

    def test_server_registers_prompts(self) -> None:
        async def run() -> tuple[set[str], str]:
            prompts = await server.mcp.list_prompts()
            rendered = await server.mcp.render_prompt(
                "buzz.summarize_submission",
                {"enrollmentid": "4317", "itemid": "assign12", "entityid": "4378"},
            )
            return (
                {prompt.name for prompt in prompts},
                rendered.messages[0].content.text,
            )

        prompt_names, prompt_text = asyncio.run(run())

        self.assertIn("buzz.summarize_submission", prompt_names)
        self.assertIn("buzz.draft_student_feedback", prompt_names)
        self.assertIn("buzz.troubleshoot_submission_access", prompt_names)
        self.assertIn("buzz.get_submission_report", prompt_text)
        self.assertIn("4317", prompt_text)

    def test_mcp_tool_call_returns_structured_activity(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.get_activity",
                    {"entityid": "4378", "itemid": "assign12"},
                )
            return result.structured_content

        activity = asyncio.run(run())

        self.assertEqual(activity["entityid"], "4378")
        self.assertEqual(activity["id"], "assign12")

    def test_mcp_tool_call_returns_structured_activity_list(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.list_activities",
                    {"entityid": "4378"},
                )
            return result.structured_content

        manifest = asyncio.run(run())

        self.assertEqual(manifest["entityid"], "4378")
        self.assertEqual(manifest["count"], 2)
        self.assertEqual(
            [activity["id"] for activity in manifest["activities"]],
            ["assign12", "lesson1"],
        )

    def test_course_manifest_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource(
                    "buzz://course/4378/manifest"
                )
            return json.loads(result.contents[0].content)

        manifest = asyncio.run(run())

        self.assertEqual(
            [activity["id"] for activity in manifest["activities"]],
            ["assign12", "lesson1"],
        )

    def test_submission_report_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource(
                    "buzz://submission/4317/assign12/report?entityid=4378"
                )
            return json.loads(result.contents[0].content)

        report = asyncio.run(run())

        self.assertEqual(report["activity_title"], "Assignment 12")
        self.assertEqual(report["q_and_a_pairs"][0]["answer"], "Yes")


if __name__ == "__main__":
    unittest.main()
