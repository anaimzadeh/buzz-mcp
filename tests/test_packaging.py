from __future__ import annotations

import json
import pathlib
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


if __name__ == "__main__":
    unittest.main()
