from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from buzz_submission_mcp.buzz_client import (
    BuzzApiError,
    BuzzClient,
    BuzzCredentials,
    _raise_for_dlap_error,
    redact_secrets,
)


class BuzzClientSecurityTests(unittest.TestCase):
    def test_redact_secrets_removes_query_xml_and_json_values(self) -> None:
        text = (
            "https://api.example/cmd?cmd=x&_token=abc123&password=secret "
            "<request password=\"secret\" token='abc123' /> "
            "{\"access_token\":\"abc123\",\"refresh_token\":\"def456\"}"
        )

        redacted = redact_secrets(text)

        self.assertNotIn("abc123", redacted)
        self.assertNotIn("secret", redacted)
        self.assertNotIn("def456", redacted)
        self.assertIn("_token=[REDACTED]", redacted)
        self.assertIn("password=[REDACTED]", redacted)
        self.assertIn('password="[REDACTED]"', redacted)
        self.assertIn("token='[REDACTED]'", redacted)
        self.assertIn('"access_token":"[REDACTED]"', redacted)

    def test_error_payload_has_stable_shape(self) -> None:
        error = BuzzApiError(
            "Missing credentials",
            code="AUTH_REQUIRED",
            details={"missing_env": ["BUZZ_USERNAME"]},
        )

        self.assertEqual(
            error.to_dict(),
            {
                "code": "AUTH_REQUIRED",
                "message": "Missing credentials",
                "retryable": False,
                "details": {"missing_env": ["BUZZ_USERNAME"]},
            },
        )

    def test_missing_credentials_are_auth_required(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "BUZZ_USERNAME": "",
                "BUZZ_PASSWORD": "",
                "BUZZ_DOMAIN": "",
            },
        ):
            with self.assertRaises(BuzzApiError) as raised:
                BuzzCredentials.from_env()

        self.assertEqual(raised.exception.code, "AUTH_REQUIRED")
        self.assertEqual(
            raised.exception.details,
            {"missing_env": ["BUZZ_USERNAME", "BUZZ_PASSWORD", "BUZZ_DOMAIN"]},
        )

    def test_http_error_body_is_redacted(self) -> None:
        class FailingClient(BuzzClient):
            def _open_url(self, request):  # type: ignore[no-untyped-def]
                raise HTTPError(
                    request.full_url,
                    403,
                    "Forbidden",
                    {},
                    BytesIO(b"bad _token=abc123 password=secret"),
                )

        client = FailingClient(
            credentials=BuzzCredentials("teacher", "secret", "domain")
        )

        with self.assertRaises(BuzzApiError) as raised:
            client._request_text("GetItem", "https://api.example/cmd", method="GET")

        message = str(raised.exception)
        self.assertEqual(raised.exception.code, "INSUFFICIENT_BUZZ_RIGHTS")
        self.assertEqual(
            raised.exception.details,
            {"command": "GetItem", "http_status": 403},
        )
        self.assertNotIn("abc123", message)
        self.assertNotIn("secret", message)
        self.assertIn("_token=[REDACTED]", message)

    def test_http_rate_limit_is_retryable(self) -> None:
        class FailingClient(BuzzClient):
            def _open_url(self, request):  # type: ignore[no-untyped-def]
                raise HTTPError(
                    request.full_url,
                    429,
                    "Too Many Requests",
                    {},
                    BytesIO(b"too many requests"),
                )

        client = FailingClient(
            credentials=BuzzCredentials("teacher", "secret", "domain")
        )

        with self.assertRaises(BuzzApiError) as raised:
            client._request_text("GetItem", "https://api.example/cmd", method="GET")

        self.assertEqual(raised.exception.code, "RATE_LIMITED")
        self.assertTrue(raised.exception.retryable)

    def test_url_error_reason_is_redacted(self) -> None:
        class FailingClient(BuzzClient):
            def _open_url(self, request):  # type: ignore[no-untyped-def]
                raise URLError("failed for _token=abc123")

        client = FailingClient(
            credentials=BuzzCredentials("teacher", "secret", "domain")
        )

        with self.assertRaises(BuzzApiError) as raised:
            client._request_text("GetItem", "https://api.example/cmd", method="GET")

        self.assertEqual(raised.exception.code, "BUZZ_API_ERROR")
        self.assertTrue(raised.exception.retryable)
        self.assertNotIn("abc123", str(raised.exception))
        self.assertIn("_token=[REDACTED]", str(raised.exception))

    def test_dlap_error_message_is_redacted(self) -> None:
        root = ET.fromstring(
            '<response code="Denied" message="bad _token=abc123 password=secret" />'
        )

        with self.assertRaises(BuzzApiError) as raised:
            _raise_for_dlap_error(root, "GetItem")

        message = str(raised.exception)
        self.assertEqual(raised.exception.code, "AUTH_REQUIRED")
        self.assertNotIn("abc123", message)
        self.assertNotIn("secret", message)
        self.assertIn("_token=[REDACTED]", message)


if __name__ == "__main__":
    unittest.main()
