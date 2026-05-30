from __future__ import annotations

import json
import pathlib
import re
import tomllib
import unittest

import buzz_submission_mcp.server as server


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pyproject_exposes_stdio_console_scripts(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

        self.assertEqual(pyproject["project"]["name"], "agilix-buzz-mcp")
        self.assertEqual(
            pyproject["project"]["scripts"],
            {
                "agilix-buzz-mcp": "buzz_submission_mcp.server:main",
                "buzz-mcp": "buzz_submission_mcp.server:main",
            },
        )

    def test_server_main_is_callable_entrypoint(self) -> None:
        self.assertTrue(callable(server.main))

    def test_registry_metadata_matches_package_and_readme_marker(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
        registry = json.loads((ROOT / "server.json").read_text())
        readme = (ROOT / "README.md").read_text()

        self.assertEqual(
            registry["$schema"],
            "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        )
        self.assertEqual(registry["name"], "io.github.anaimzadeh/agilix-buzz-mcp")
        self.assertIn(f"mcp-name: {registry['name']}", readme)
        self.assertEqual(registry["version"], pyproject["project"]["version"])
        self.assertEqual(len(registry["packages"]), 1)

        package = registry["packages"][0]
        self.assertEqual(package["registryType"], "pypi")
        self.assertEqual(package["identifier"], pyproject["project"]["name"])
        self.assertEqual(package["version"], pyproject["project"]["version"])
        self.assertEqual(package["transport"], {"type": "stdio"})

    def test_dockerfile_builds_stdio_runtime_from_local_package(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text()

        self.assertIn("FROM python:3.11-slim AS runtime", dockerfile)
        self.assertIn("COPY pyproject.toml README.md ./", dockerfile)
        self.assertIn("COPY src ./src", dockerfile)
        self.assertIn("RUN pip install --no-cache-dir .", dockerfile)
        self.assertIn('ENTRYPOINT ["agilix-buzz-mcp"]', dockerfile)
        self.assertIn("USER 65532:65532", dockerfile)

    def test_dockerignore_excludes_local_secrets_and_build_artifacts(self) -> None:
        ignored = set((ROOT / ".dockerignore").read_text().splitlines())

        for pattern in {
            ".env",
            ".env.*",
            ".git/",
            ".venv/",
            "__pycache__/",
            "*.egg-info/",
            "build/",
            "dist/",
        }:
            self.assertIn(pattern, ignored)

    def test_source_distribution_manifest_includes_release_artifacts(self) -> None:
        manifest = (ROOT / "MANIFEST.in").read_text()

        self.assertIn("include server.json", manifest)
        self.assertIn("recursive-include scripts *.py", manifest)
        self.assertIn("recursive-include docs/specs *.md", manifest)

    def test_ci_workflow_runs_release_gate_checks(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()

        self.assertIn("name: CI", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn("actions/setup-node@v4", workflow)
        self.assertIn('python-version: "3.11"', workflow)
        self.assertIn('node-version: "22"', workflow)
        self.assertIn(
            "env PYTHONPATH=src uv run python -m unittest discover -s tests",
            workflow,
        )
        self.assertIn("uv build", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("docker build -t agilix-buzz-mcp:ci .", workflow)
        self.assertIn("python scripts/mcp_inspector_smoke.py", workflow)
        self.assertRegex(workflow, re.compile(r"permissions:\s+contents: read", re.S))

    def test_live_sandbox_workflow_runs_credentialed_release_gate(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "live-sandbox.yml").read_text()

        self.assertIn("name: Live Buzz Sandbox", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("environment: buzz-sandbox", workflow)
        self.assertIn('BUZZ_RUN_LIVE_TESTS: "1"', workflow)
        self.assertIn("BUZZ_USERNAME: ${{ secrets.BUZZ_USERNAME }}", workflow)
        self.assertIn("BUZZ_PASSWORD: ${{ secrets.BUZZ_PASSWORD }}", workflow)
        self.assertIn("BUZZ_TEST_ENTITYID: ${{ secrets.BUZZ_TEST_ENTITYID }}", workflow)
        self.assertIn("BUZZ_TEST_DOMAINID: ${{ secrets.BUZZ_TEST_DOMAINID }}", workflow)
        self.assertIn("BUZZ_TEST_USERID: ${{ secrets.BUZZ_TEST_USERID }}", workflow)
        self.assertIn(
            "BUZZ_TEST_SANDBOX_ACK: ${{ vars.BUZZ_TEST_SANDBOX_ACK }}",
            workflow,
        )
        self.assertIn("python scripts/check_live_buzz_env.py", workflow)
        self.assertIn(
            "env PYTHONPATH=src uv run python -m unittest tests.test_live_buzz",
            workflow,
        )
        self.assertRegex(workflow, re.compile(r"permissions:\s+contents: read", re.S))


if __name__ == "__main__":
    unittest.main()
