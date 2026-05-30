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

COURSE = {
    "entityid": "4378",
    "title": "Algebra I",
    "type": "Course",
    "domainid": "100",
    "reference": "ALG-1",
    "guid": "course-guid",
    "baseid": "200",
    "start_date": "2025-08-01T00:00:00Z",
    "end_date": "2026-05-30T00:00:00Z",
    "days": "304",
    "term": "Fall",
    "version": "12",
}

USER = {
    "id": "9001",
    "display_name": "Sally Johnson",
    "reference": "student-ref",
    "domainid": "100",
    "guid": "user-guid",
    "version": "7",
    "pii_redacted": True,
}

ENROLLMENT = {
    "enrollmentid": "4317",
    "entityid": "4378",
    "userid": "9001",
    "role": "Student",
    "roleid": "",
    "privileges": "Student",
    "status": "1",
    "domainid": "100",
    "reference": "student-ref",
    "guid": "enrollment-guid",
    "start_date": "2025-08-01T00:00:00Z",
    "end_date": "2026-05-30T00:00:00Z",
    "first_activity_date": "2025-08-10T12:00:00Z",
    "last_activity_date": "2025-09-01T12:00:00Z",
    "version": "4",
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

    def get_course(
        self, *, courseid: str, version: str | None = None
    ) -> dict[str, object]:
        course = dict(COURSE)
        course["entityid"] = courseid
        if version is not None:
            course["version"] = version
        return course

    def list_courses(self, **kwargs: object) -> dict[str, object]:
        course = dict(COURSE)
        course["domainid"] = kwargs["domainid"]
        return {
            "domainid": kwargs["domainid"],
            "includedescendantdomains": kwargs["includedescendantdomains"],
            "show": kwargs["show"],
            "text": kwargs.get("text") or "",
            "count": 1,
            "limit": kwargs["limit"],
            "courses": [course],
        }

    def get_user(self, *, userid: str) -> dict[str, object]:
        user = dict(USER)
        user["id"] = userid
        return user

    def get_enrollment(self, *, enrollmentid: str) -> dict[str, object]:
        enrollment = dict(ENROLLMENT)
        enrollment["enrollmentid"] = enrollmentid
        return enrollment

    def list_user_enrollments(self, **kwargs: object) -> dict[str, object]:
        enrollment = dict(ENROLLMENT)
        enrollment["userid"] = kwargs["userid"]
        return {
            "userid": kwargs["userid"],
            "count": 1,
            "limit": kwargs["limit"],
            "enrollments": [enrollment],
        }

    def list_entity_enrollments(self, **kwargs: object) -> dict[str, object]:
        enrollment = dict(ENROLLMENT)
        enrollment["entityid"] = kwargs["entityid"]
        return {
            "entityid": kwargs["entityid"],
            "count": 1,
            "limit": kwargs["limit"],
            "enrollments": [enrollment],
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
            "buzz.get_course",
            "buzz.list_courses",
            "buzz.get_user",
            "buzz.get_enrollment",
            "buzz.list_user_enrollments",
            "buzz.list_entity_enrollments",
            "buzz.get_submission_report",
            "buzz.get_attachment_url",
            "buzz.docs.search",
            "buzz.docs.get_command",
            "buzz.docs.get_schema",
            "get_complete_submission_report",
        }:
            self.assertIn(name, tools)
            self.assertTrue(tools[name].output_schema)
        self.assertEqual(
            tools["buzz.get_attachment_url"].parameters["properties"]["source"]["enum"],
            ["submission", "attempt-question"],
        )
        self.assertEqual(
            tools["buzz.docs.search"].parameters["properties"]["entry_type"]["enum"],
            ["any", "command", "schema", "enum", "concept"],
        )
        self.assertEqual(
            tools["buzz.list_courses"].parameters["properties"]["show"]["enum"],
            ["current", "active"],
        )

    def test_server_registers_resource_templates(self) -> None:
        async def run() -> set[str]:
            templates = await server.mcp.list_resource_templates()
            return {template.uri_template for template in templates}

        templates = asyncio.run(run())

        self.assertIn("buzz://course/{entityid}/item/{itemid}", templates)
        self.assertIn("buzz://course/{entityid}/manifest", templates)
        self.assertIn("buzz://course/{entityid}", templates)
        self.assertIn("buzz://domain/{domainid}/courses", templates)
        self.assertIn("buzz://user/{userid}", templates)
        self.assertIn("buzz://enrollment/{enrollmentid}", templates)
        self.assertIn("buzz://user/{userid}/enrollments", templates)
        self.assertIn("buzz://course/{entityid}/enrollments", templates)
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

    def test_mcp_tool_call_returns_structured_course(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.get_course",
                    {"courseid": "4378", "version": "12"},
                )
            return result.structured_content

        course = asyncio.run(run())

        self.assertEqual(course["entityid"], "4378")
        self.assertEqual(course["title"], "Algebra I")
        self.assertEqual(course["version"], "12")

    def test_mcp_tool_call_returns_structured_course_list(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.list_courses",
                    {"domainid": "100", "show": "active", "limit": 10},
                )
            return result.structured_content

        payload = asyncio.run(run())

        self.assertEqual(payload["domainid"], "100")
        self.assertEqual(payload["show"], "active")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["courses"][0]["entityid"], "4378")

    def test_mcp_tool_call_returns_privacy_redacted_user(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.get_user",
                    {"userid": "9001"},
                )
            return result.structured_content

        user = asyncio.run(run())

        self.assertEqual(user["id"], "9001")
        self.assertEqual(user["display_name"], "Sally Johnson")
        self.assertTrue(user["pii_redacted"])

    def test_mcp_tool_call_returns_structured_entity_enrollments(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.call_tool(
                    "buzz.list_entity_enrollments",
                    {"entityid": "4378", "limit": 10},
                )
            return result.structured_content

        payload = asyncio.run(run())

        self.assertEqual(payload["entityid"], "4378")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["enrollments"][0]["enrollmentid"], "4317")

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

    def test_course_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource("buzz://course/4378")
            return json.loads(result.contents[0].content)

        course = asyncio.run(run())

        self.assertEqual(course["entityid"], "4378")
        self.assertEqual(course["title"], "Algebra I")

    def test_domain_courses_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource("buzz://domain/100/courses")
            return json.loads(result.contents[0].content)

        payload = asyncio.run(run())

        self.assertEqual(payload["domainid"], "100")
        self.assertEqual(payload["courses"][0]["title"], "Algebra I")

    def test_user_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource("buzz://user/9001")
            return json.loads(result.contents[0].content)

        user = asyncio.run(run())

        self.assertEqual(user["id"], "9001")
        self.assertTrue(user["pii_redacted"])

    def test_course_enrollments_resource_returns_json_content(self) -> None:
        async def run() -> dict[str, object]:
            with patch.object(server, "_service", return_value=FakeService()):
                result = await server.mcp.read_resource(
                    "buzz://course/4378/enrollments"
                )
            return json.loads(result.contents[0].content)

        payload = asyncio.run(run())

        self.assertEqual(payload["entityid"], "4378")
        self.assertEqual(payload["enrollments"][0]["userid"], "9001")

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

    def test_mcp_docs_search_returns_structured_metadata(self) -> None:
        async def run() -> dict[str, object]:
            result = await server.mcp.call_tool(
                "buzz.docs.search",
                {
                    "query": "student submission",
                    "entry_type": "command",
                    "limit": 5,
                },
            )
            return result.structured_content

        payload = asyncio.run(run())

        self.assertEqual(payload["query"], "student submission")
        names = [entry["name"] for entry in payload["results"]]
        self.assertIn("GetStudentSubmission", names)

    def test_mcp_docs_get_schema_returns_structured_metadata(self) -> None:
        async def run() -> dict[str, object]:
            result = await server.mcp.call_tool(
                "buzz.docs.get_schema",
                {"name": "Submission"},
            )
            return result.structured_content

        payload = asyncio.run(run())

        self.assertEqual(payload["name"], "Submission")
        self.assertEqual(payload["path"], "Schema/Submission")
        self.assertTrue(payload["sensitive"])


if __name__ == "__main__":
    unittest.main()
