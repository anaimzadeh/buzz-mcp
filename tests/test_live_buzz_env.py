from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_live_buzz_env.py"
SPEC = importlib.util.spec_from_file_location("check_live_buzz_env", SCRIPT_PATH)
assert SPEC is not None
live_env = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(live_env)


class LiveBuzzEnvTests(unittest.TestCase):
    def test_missing_live_env_reports_gate_flag_credentials_and_sandbox_ack(self) -> None:
        missing = live_env.missing_live_env({})

        self.assertEqual(
            missing,
            [
                "BUZZ_RUN_LIVE_TESTS=1",
                "BUZZ_USERNAME",
                "BUZZ_PASSWORD",
                "BUZZ_DOMAIN",
                "BUZZ_TEST_ENTITYID",
                "BUZZ_TEST_ITEMID",
                "BUZZ_TEST_ENROLLMENTID",
                "BUZZ_TEST_SANDBOX_ACK=1",
            ],
        )

    def test_missing_live_env_accepts_complete_required_configuration(self) -> None:
        env = {
            "BUZZ_RUN_LIVE_TESTS": "1",
            "BUZZ_USERNAME": "teacher",
            "BUZZ_PASSWORD": "secret",
            "BUZZ_DOMAIN": "school",
            "BUZZ_TEST_ENTITYID": "course",
            "BUZZ_TEST_ITEMID": "item",
            "BUZZ_TEST_ENROLLMENTID": "enrollment",
            "BUZZ_TEST_SANDBOX_ACK": "1",
        }

        self.assertEqual(live_env.missing_live_env(env), [])

    def test_main_does_not_print_secret_values_when_configuration_is_missing(self) -> None:
        stderr = io.StringIO()
        with patch.dict(
            "os.environ",
            {
                "BUZZ_RUN_LIVE_TESTS": "1",
                "BUZZ_USERNAME": "teacher",
                "BUZZ_PASSWORD": "super-secret",
                "BUZZ_DOMAIN": "school",
                "BUZZ_TEST_ENTITYID": "course",
            },
            clear=True,
        ):
            with contextlib.redirect_stderr(stderr):
                result = live_env.main()

        self.assertEqual(result, 1)
        error_output = stderr.getvalue()
        self.assertIn("BUZZ_TEST_ITEMID", error_output)
        self.assertIn("BUZZ_TEST_SANDBOX_ACK=1", error_output)
        self.assertNotIn("super-secret", error_output)


if __name__ == "__main__":
    unittest.main()
