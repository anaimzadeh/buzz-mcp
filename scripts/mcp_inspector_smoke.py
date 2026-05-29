from __future__ import annotations

import json
import os
import pathlib
import shlex
import subprocess
import sys
from collections.abc import Mapping
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEFAULT_INSPECTOR_PACKAGE = "@modelcontextprotocol/inspector@0.21.2"
DEFAULT_SERVER_ARGS = "-m buzz_submission_mcp.server"

EXPECTED_TOOLS = frozenset(
    {
        "buzz.get_activity",
        "buzz.list_activities",
        "buzz.get_submission_report",
        "buzz.get_attachment_url",
        "buzz.docs.search",
        "buzz.docs.get_command",
        "buzz.docs.get_schema",
        "get_complete_submission_report",
    }
)
EXPECTED_RESOURCE_TEMPLATES = frozenset(
    {
        "buzz.activity",
        "buzz.course_manifest",
        "buzz.submission_report",
    }
)
EXPECTED_PROMPTS = frozenset(
    {
        "buzz.summarize_submission",
        "buzz.draft_student_feedback",
        "buzz.troubleshoot_submission_access",
    }
)

METHOD_EXPECTATIONS = {
    "tools/list": ("tools", EXPECTED_TOOLS),
    "resources/templates/list": ("resourceTemplates", EXPECTED_RESOURCE_TEMPLATES),
    "prompts/list": ("prompts", EXPECTED_PROMPTS),
}


def build_command(method: str, environ: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    inspector_package = env.get("MCP_INSPECTOR_PACKAGE", DEFAULT_INSPECTOR_PACKAGE)
    server_command = shlex.split(env.get("MCP_INSPECTOR_SERVER_COMMAND", sys.executable))
    server_args = shlex.split(env.get("MCP_INSPECTOR_SERVER_ARGS", DEFAULT_SERVER_ARGS))

    return [
        "npx",
        "-y",
        inspector_package,
        "--cli",
        *server_command,
        *server_args,
        "--method",
        method,
    ]


def build_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if environ is None else environ)
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC) if not pythonpath else f"{SRC}{os.pathsep}{pythonpath}"
    env.setdefault("NPM_CONFIG_LOGLEVEL", "error")
    return env


def run_inspector(method: str) -> dict[str, Any]:
    timeout = float(os.environ.get("MCP_INSPECTOR_TIMEOUT_SECONDS", "45"))
    command = build_command(method)

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=build_env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Inspector method {method!r} timed out after {timeout}s") from exc

    if result.returncode != 0:
        message = [
            f"Inspector method {method!r} failed with exit code {result.returncode}.",
            "stdout:",
            result.stdout.strip(),
            "stderr:",
            result.stderr.strip(),
        ]
        raise RuntimeError("\n".join(message))

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Inspector method {method!r} returned non-JSON output: {result.stdout!r}"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Inspector method {method!r} returned {type(payload).__name__}")
    return payload


def validate_payload(method: str, payload: Mapping[str, Any]) -> None:
    collection_key, expected_names = METHOD_EXPECTATIONS[method]
    collection = payload.get(collection_key)

    if not isinstance(collection, list):
        raise AssertionError(f"{method} did not return a {collection_key!r} list")

    names = {
        item.get("name")
        for item in collection
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    missing = sorted(expected_names - names)
    if missing:
        raise AssertionError(f"{method} missing expected names: {', '.join(missing)}")


def main() -> int:
    failures: list[str] = []

    for method in METHOD_EXPECTATIONS:
        try:
            payload = run_inspector(method)
            validate_payload(method, payload)
            print(f"ok {method}")
        except Exception as exc:  # pragma: no cover - exercised by CI failures.
            failures.append(f"{method}: {exc}")

    if failures:
        print("MCP Inspector smoke test failed.", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("MCP Inspector smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
