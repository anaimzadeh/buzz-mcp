from __future__ import annotations

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SMOKE_PATH = ROOT / "scripts" / "mcp_inspector_smoke.py"
SPEC = importlib.util.spec_from_file_location("mcp_inspector_smoke", SMOKE_PATH)
assert SPEC is not None
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(smoke)


class McpInspectorSmokeTests(unittest.TestCase):
    def test_build_command_defaults_to_pinned_inspector_and_module_server(self) -> None:
        command = smoke.build_command("tools/list", {})

        self.assertEqual(
            command[:4], ["npx", "-y", smoke.DEFAULT_INSPECTOR_PACKAGE, "--cli"]
        )
        self.assertIn("@modelcontextprotocol/inspector@0.21.2", command)
        self.assertTrue(command[4])
        self.assertEqual(
            command[-4:],
            ["-m", "buzz_submission_mcp.server", "--method", "tools/list"],
        )

    def test_build_command_allows_server_override(self) -> None:
        command = smoke.build_command(
            "prompts/list",
            {
                "MCP_INSPECTOR_PACKAGE": "@modelcontextprotocol/inspector@0.21.2",
                "MCP_INSPECTOR_SERVER_COMMAND": "uv",
                "MCP_INSPECTOR_SERVER_ARGS": "run agilix-buzz-mcp",
            },
        )

        self.assertEqual(
            command,
            [
                "npx",
                "-y",
                "@modelcontextprotocol/inspector@0.21.2",
                "--cli",
                "uv",
                "run",
                "agilix-buzz-mcp",
                "--method",
                "prompts/list",
            ],
        )

    def test_build_env_prepends_source_path(self) -> None:
        env = smoke.build_env({"PYTHONPATH": "existing"})

        self.assertTrue(env["PYTHONPATH"].startswith(str(ROOT / "src")))
        self.assertTrue(env["PYTHONPATH"].endswith("existing"))
        self.assertEqual(env["NPM_CONFIG_LOGLEVEL"], "error")

    def test_validate_payload_accepts_expected_capabilities(self) -> None:
        smoke.validate_payload(
            "tools/list",
            {"tools": [{"name": name} for name in smoke.EXPECTED_TOOLS]},
        )
        smoke.validate_payload(
            "resources/templates/list",
            {
                "resourceTemplates": [
                    {"name": name} for name in smoke.EXPECTED_RESOURCE_TEMPLATES
                ]
            },
        )
        smoke.validate_payload(
            "prompts/list",
            {"prompts": [{"name": name} for name in smoke.EXPECTED_PROMPTS]},
        )

    def test_validate_payload_reports_missing_expected_capability(self) -> None:
        with self.assertRaisesRegex(AssertionError, "buzz.get_activity"):
            smoke.validate_payload("tools/list", {"tools": []})


if __name__ == "__main__":
    unittest.main()
